/*--------------------------------------------------------------------------
  _____       ______________
 |  __ \   /\|__   ____   __|
 | |__) | /  \  | |    | |
 |  _  / / /\ \ | |    | |
 | | \ \/ ____ \| |    | |
 |_|  \_\/    \_\_|    |_|    ... RFID ALL THE THINGS!

 A resource access control and telemetry solution for Makerspaces

 Developed at MakeIt Labs - New Hampshire's First & Largest Makerspace
 http://www.makeitlabs.com/

 Copyright 2017-2020 MakeIt Labs

 Permission is hereby granted, free of charge, to any person obtaining a
 copy of this software and associated documentation files (the "Software"),
 to deal in the Software without restriction, including without limitation
 the rights to use, copy, modify, merge, publish, distribute, sublicense,
 and/or sell copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

 --------------------------------------------------------------------------
 Author: Steve Richardson (steve.richardson@makeitlabs.com)
 -------------------------------------------------------------------------- */

#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_system.h"
#include "https.h"
#include "sdcard.h"

#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include "lwip/netdb.h"
#include "lwip/dns.h"
#include "lwip/ip4_addr.h"

#include "mbedtls/platform.h"
#include "mbedtls/net.h"
#include "mbedtls/debug.h"
#include "mbedtls/ssl.h"
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/error.h"
#include "mbedtls/certs.h"
#include "mbedtls/base64.h"

#include "mqtt_client.h"

#include "display_task.h"
#include "rfid_task.h"
#include "net_task.h"

static const char *TAG = "net_task";

void net_timer(TimerHandle_t xTimer);


extern const uint8_t client_cert_pem_start[] asm("_binary_client_uratt_crt_start");
extern const uint8_t client_cert_pem_end[] asm("_binary_client_uratt_crt_end");
extern const uint8_t client_key_pem_start[] asm("_binary_client_uratt_key_start");
extern const uint8_t client_key_pem_end[] asm("_binary_client_uratt_key_end");
extern const uint8_t ca_cert_pem_start[] asm("_binary_ca_crt_start");
extern const uint8_t ca_cert_pem_end[] asm("_binary_ca_crt_end");


// The examples use simple configurations that you can set via 'make menuconfig'.
#define EXAMPLE_WIFI_SSID CONFIG_WIFI_SSID
#define EXAMPLE_WIFI_PASS CONFIG_WIFI_PASSWORD
#define WEB_SERVER CONFIG_WEB_SERVER
#define WEB_PORT CONFIG_WEB_PORT
#define WEB_URL_PATH CONFIG_WEB_URL_PATH
#define WEB_BASIC_AUTH_USER CONFIG_WEB_BASIC_AUTH_USER
#define WEB_BASIC_AUTH_PASS CONFIG_WEB_BASIC_AUTH_PASS


// FreeRTOS event group to signal when we are connected & ready to make a request
static EventGroupHandle_t wifi_event_group;

// The event group allows multiple bits for each event,
// but we only care about one event - are we connected
// to the AP with an IP?
const int CONNECTED_BIT = BIT0;

esp_mqtt_client_handle_t mqtt_client;

#define NET_QUEUE_DEPTH 16

typedef struct net_evt {
  uint8_t cmd;
} net_evt_t;

static QueueHandle_t m_q;

#define NET_CMD_DOWNLOAD_ACL  1
#define NET_CMD_SEND_ACL_UPDATED 2
#define NET_CMD_SEND_WIFI_STR 3


static esp_err_t net_mqtt_event_handler(esp_mqtt_event_handle_t event)
{
    esp_mqtt_client_handle_t client = event->client;
    int msg_id;
    // your_context_t *context = event->context;
    switch (event->event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI(TAG, "MQTT_EVENT_CONNECTED");
            msg_id = esp_mqtt_client_subscribe(client, "ratt/control/broadcast/acl/update", 0);
            ESP_LOGI(TAG, "sent subscribe successful, msg_id=%d", msg_id);
            break;
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGI(TAG, "MQTT_EVENT_DISCONNECTED");
            break;

        case MQTT_EVENT_SUBSCRIBED:
            ESP_LOGI(TAG, "MQTT_EVENT_SUBSCRIBED, msg_id=%d", event->msg_id);
            //msg_id = esp_mqtt_client_publish(client, "/topic/qos0", "data", 0, 0, 0);
            //ESP_LOGI(TAG, "sent publish successful, msg_id=%d", msg_id);
            break;
        case MQTT_EVENT_UNSUBSCRIBED:
            ESP_LOGI(TAG, "MQTT_EVENT_UNSUBSCRIBED, msg_id=%d", event->msg_id);
            break;
        case MQTT_EVENT_PUBLISHED:
            ESP_LOGI(TAG, "MQTT_EVENT_PUBLISHED, msg_id=%d", event->msg_id);
            break;
        case MQTT_EVENT_DATA:
            ESP_LOGI(TAG, "MQTT_EVENT_DATA");
            printf("TOPIC=%.*s\r\n", event->topic_len, event->topic);
            printf("DATA=%.*s\r\n", event->data_len, event->data);

            net_cmd_queue(NET_CMD_DOWNLOAD_ACL);
            break;
        case MQTT_EVENT_ERROR:
            ESP_LOGI(TAG, "MQTT_EVENT_ERROR");
            break;
        default:
            ESP_LOGI(TAG, "Other event id:%d", event->event_id);
            break;
    }
    return ESP_OK;
}


static esp_err_t event_handler(void *ctx, system_event_t *event)
{
    char s[32];
    const ip4_addr_t* ip;

    switch(event->event_id) {
    case SYSTEM_EVENT_WIFI_READY:
        display_wifi_msg("WIFI READY");
        break;
    case SYSTEM_EVENT_STA_START:
        display_wifi_msg("WIFI CONNECT");
        esp_wifi_connect();
        break;
    case SYSTEM_EVENT_STA_GOT_IP:
        ip = &event->event_info.got_ip.ip_info.ip;
        snprintf(s, sizeof(s), "%d.%d.%d.%d", ip4_addr1_16(ip), ip4_addr2_16(ip), ip4_addr3_16(ip), ip4_addr4_16(ip));
        display_wifi_msg(s);

        xEventGroupSetBits(wifi_event_group, CONNECTED_BIT);
        break;
    case SYSTEM_EVENT_STA_DISCONNECTED:
        /* This is a workaround as ESP32 WiFi libs don't currently
           auto-reassociate. */
        display_wifi_msg("WIFI DISCON");

        esp_wifi_connect();
        xEventGroupClearBits(wifi_event_group, CONNECTED_BIT);
        break;
    default:
        break;
    }
    return ESP_OK;
}



BaseType_t net_cmd_queue(int cmd)
{
    net_evt_t evt;
    evt.cmd = cmd;
    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}

void net_init(void)
{
    char s[32];

    ESP_LOGI(TAG, "Initializing network...");

    m_q = xQueueCreate(NET_QUEUE_DEPTH, sizeof(net_evt_t));
    if (m_q == NULL) {
        ESP_LOGE(TAG, "FATAL: Cannot create net queue!");
    }

    display_net_msg("WIFI INIT");

    tcpip_adapter_init();
    wifi_event_group = xEventGroupCreate();
    ESP_ERROR_CHECK( esp_event_loop_init(event_handler, NULL) );
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK( esp_wifi_init(&cfg) );
    ESP_ERROR_CHECK( esp_wifi_set_storage(WIFI_STORAGE_RAM) );
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = EXAMPLE_WIFI_SSID,
            .password = EXAMPLE_WIFI_PASS,
        },
    };

    snprintf(s, sizeof(s), "%s", wifi_config.sta.ssid);
    display_net_msg(s);

    ESP_LOGI(TAG, "Setting WiFi configuration SSID %s...", wifi_config.sta.ssid);
    ESP_ERROR_CHECK( esp_wifi_set_mode(WIFI_MODE_STA) );
    ESP_ERROR_CHECK( esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_config) );
    ESP_ERROR_CHECK( esp_wifi_start() );

    TimerHandle_t timer = xTimerCreate("rssi_timer", (1000 / portTICK_PERIOD_MS), pdTRUE, (void*) 0, net_timer);

    if (xTimerStart(timer, 0) != pdPASS) {
        ESP_LOGE(TAG, "Could not start net timer");
    }


    esp_log_level_set("*", ESP_LOG_INFO);
    esp_log_level_set("MQTT_CLIENT", ESP_LOG_VERBOSE);
    esp_log_level_set("TRANSPORT_TCP", ESP_LOG_VERBOSE);
    esp_log_level_set("TRANSPORT_SSL", ESP_LOG_VERBOSE);
    esp_log_level_set("TRANSPORT", ESP_LOG_VERBOSE);
    esp_log_level_set("OUTBOX", ESP_LOG_VERBOSE);

    const esp_mqtt_client_config_t mqtt_cfg = {
        .uri = "mqtts://192.168.0.153:21883",
        .event_handle = net_mqtt_event_handler,
        .client_cert_pem = (const char *)client_cert_pem_start,
        .client_key_pem = (const char *)client_key_pem_start,
        .cert_pem = (const char *)ca_cert_pem_start,
        .skip_cert_common_name_check = true,
    };

    ESP_LOGI(TAG, "[APP] Free memory: %d bytes", esp_get_free_heap_size());
    mqtt_client = esp_mqtt_client_init(&mqtt_cfg);

}


#define RESP_BUF_SIZE 1024

void net_download_acl()
{
  int ret;
  char web_url[256];
  char *resp_buf;

  resp_buf = malloc(RESP_BUF_SIZE);
  if (resp_buf) {
      ret = http_init(0);
      snprintf(web_url, sizeof(web_url), "https://%s/%s", WEB_SERVER, WEB_URL_PATH);

      display_net_msg("WIFI DOWNLOAD");

      xSemaphoreTake(g_sdcard_mutex, portMAX_DELAY);
      FILE* file = fopen("/sdcard/acl-temp.txt", "w");

      if (file) {
          ESP_LOGI(TAG, "URL: %s", web_url);
          ret = http_get(0, web_url, WEB_BASIC_AUTH_USER, WEB_BASIC_AUTH_PASS, resp_buf, RESP_BUF_SIZE, file);

          ESP_LOGI(TAG, "http_get returned %d", ret);
          if (ret == -1) {
              ESP_LOGE(TAG, "%s", resp_buf);
          }
          fclose(file);
      } else {
          ESP_LOGE(TAG, "could not open file for writing");
      }
      http_close(0);

      if (ret == 200) {
          xSemaphoreTake(g_acl_mutex, portMAX_DELAY);
          // delete existing ACL file if it exists
          struct stat st;
          if (stat("/sdcard/acl.txt", &st) == 0) {
              unlink("/sdcard/acl.txt");
          }

          // move downloaded ACL in place
          if (rename("/sdcard/acl-temp.txt", "/sdcard/acl.txt") != 0) {
              ESP_LOGE(TAG, "Could not rename downloaded ACL file!");
          }
          xSemaphoreGive(g_acl_mutex);

          display_net_msg("DOWNLOAD OK");
      } else {
          display_net_msg("DOWNLOAD FAIL");
      }

      xSemaphoreGive(g_sdcard_mutex);

      free(resp_buf);
  } else {
      ESP_LOGE(TAG, "Could not malloc acl buffer");
  }

  net_cmd_queue(NET_CMD_SEND_ACL_UPDATED);
}

void net_send_wifi_strength(void)
{
  wifi_ap_record_t wifidata;
  if (esp_wifi_sta_get_ap_info(&wifidata)==0){
    // TOPIC=ratt/status/node/b827eb206a6c/wifi/status
    // DATA={"ap": "46:D9:E7:69:BB:67", "freq": "2.412", "quality": 60, "essid": "MakeIt Members", "level": -68}

    char *topic, *payload;
    topic = malloc(128);
    payload = malloc(256);

    uint8_t mac[6];
    esp_efuse_mac_get_default(mac);

    const int chan_freq[] = { 2412, 2417, 2422, 2427, 2432, 2437, 2442, 2447, 2452, 2457, 2462, 2467, 2472, 2484 };

    snprintf(topic, 128, "ratt/status/node/%02x%02x%02x%02x%02x%02x/wifi/status", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    snprintf(payload, 256, "{\"ap\": \"%02X:%02X:%02X:%02X:%02X:%02X\", \"freq\": \"%1d.%3d\", \"essid\": \"%s\", \"level\": %d}",
      wifidata.bssid[0],wifidata.bssid[1],wifidata.bssid[2],wifidata.bssid[3],wifidata.bssid[4],wifidata.bssid[5],
      (wifidata.primary <= 16) ? chan_freq[wifidata.primary-1] / 1000 : 0, (wifidata.primary <= 16) ? chan_freq[wifidata.primary-1] % 1000 : 0,
      wifidata.ssid,
      wifidata.rssi);
    int msg_id = esp_mqtt_client_publish(mqtt_client, topic, payload, 0, 0, 0);
    ESP_LOGI(TAG, "published msg %d", msg_id);
    free(topic);
    free(payload);
  }
}


void net_send_acl_updated(void)
{
  // ratt/status/node/b827eb2f8dca/acl/update {"status":"downloaded"}

  char *topic, *payload;
  topic = malloc(128);
  payload = malloc(128);

  uint8_t mac[6];
  esp_efuse_mac_get_default(mac);

  snprintf(topic, 128, "ratt/status/node/%02x%02x%02x%02x%02x%02x/acl/update", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  snprintf(payload, 128, "{\"status\":\"downloaded\"}");
  int msg_id = esp_mqtt_client_publish(mqtt_client, topic, payload, 0, 0, 0);
  ESP_LOGI(TAG, "published msg %d", msg_id);
  free(topic);
  free(payload);


}

void net_task(void *pvParameters)
{
    ESP_LOGI(TAG, "start net task");
    net_init();

    // queue an initial ACL download
    net_cmd_queue(NET_CMD_DOWNLOAD_ACL);

    display_net_msg("WIFI CONNECT");
    // Wait for the callback to set the CONNECTED_BIT in the event group.
    xEventGroupWaitBits(wifi_event_group, CONNECTED_BIT, false, true, portMAX_DELAY);
    ESP_LOGI(TAG, "Connected to AP...");

    esp_mqtt_client_start(mqtt_client);

    while(1) {
      net_evt_t evt;

      if (xQueueReceive(m_q, &evt, (20 / portTICK_PERIOD_MS)) == pdPASS) {
        switch(evt.cmd) {
          case NET_CMD_DOWNLOAD_ACL:
            net_download_acl();
            break;

          case NET_CMD_SEND_ACL_UPDATED:
            net_send_acl_updated();
            break;

          case NET_CMD_SEND_WIFI_STR:
            net_send_wifi_strength();
            break;

          default:
            ESP_LOGE(TAG, "Unknown net event cmd %d", evt.cmd);
            break;
        }
      }
    }
}

void net_timer(TimerHandle_t xTimer)
{
    static int interval = 0;

    wifi_ap_record_t wifidata;
    if (esp_wifi_sta_get_ap_info(&wifidata)==0){
        display_wifi_rssi(wifidata.rssi);

        if (interval % 20 == 0) {
          net_cmd_queue(NET_CMD_SEND_WIFI_STR);
          interval = 0;
        }
        interval++;

    }
}







#ifdef MBEDTLS_DEBUG_C
#define MBEDTLS_DEBUG_LEVEL 4

/* mbedtls debug function that translates mbedTLS debug output
   to ESP_LOGx debug output.

   MBEDTLS_DEBUG_LEVEL 4 means all mbedTLS debug output gets sent here,
   and then filtered to the ESP logging mechanism.
*/
static void mbedtls_debug(void *ctx, int level, const char *file, int line, const char *str)
{
    const char *MBTAG = "mbedtls";
    char *file_sep;

    /* Shorten 'file' from the whole file path to just the filename
       This is a bit wasteful because the macros are compiled in with
       the full _FILE_ path in each case.
    */
    file_sep = rindex(file, '/');
    if(file_sep)
        file = file_sep+1;

    switch(level) {
    case 1:
        ESP_LOGI(MBTAG, "%s:%d %s", file, line, str);
        break;
    case 2:
    case 3:
        ESP_LOGD(MBTAG, "%s:%d %s", file, line, str);
    case 4:
        ESP_LOGV(MBTAG, "%s:%d %s", file, line, str);
        break;
    default:
        ESP_LOGE(MBTAG, "Unexpected log level %d: %s", level, str);
        break;
    }
}

#endif
