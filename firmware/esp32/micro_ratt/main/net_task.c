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


#include "display_task.h"
#include "rfid_task.h"
#include "net_task.h"
#include "net_https.h"
#include "net_mqtt.h"

static const char *TAG = "net_task";

void net_timer(TimerHandle_t xTimer);

// The examples use simple configurations that you can set via 'make menuconfig'.
#define EXAMPLE_WIFI_SSID CONFIG_WIFI_SSID
#define EXAMPLE_WIFI_PASS CONFIG_WIFI_PASSWORD

// FreeRTOS event group to signal when we are connected & ready to make a request
static EventGroupHandle_t wifi_event_group;

// The event group allows multiple bits for each event,
// but we only care about one event - are we connected
// to the AP with an IP?
const int CONNECTED_BIT = BIT0;


#define NET_QUEUE_DEPTH 16

typedef struct net_evt {
  uint8_t cmd;
} net_evt_t;

static QueueHandle_t m_q;

uint8_t g_mac_addr[6];



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

    // get MAC address from efuse
    esp_efuse_mac_get_default(g_mac_addr);

    TimerHandle_t timer = xTimerCreate("rssi_timer", (1000 / portTICK_PERIOD_MS), pdTRUE, (void*) 0, net_timer);

    if (xTimerStart(timer, 0) != pdPASS) {
        ESP_LOGE(TAG, "Could not start net timer");
    }

    net_https_init();
    net_mqtt_init();
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

    net_mqtt_start();

    while(1) {
      net_evt_t evt;

      if (xQueueReceive(m_q, &evt, (20 / portTICK_PERIOD_MS)) == pdPASS) {
        switch(evt.cmd) {
          case NET_CMD_DOWNLOAD_ACL:
            net_https_download_acl();
            break;

          case NET_CMD_SEND_ACL_UPDATED:
            net_mqtt_send_acl_updated(MQTT_ACL_SUCCESS);
            break;

          case NET_CMD_SEND_ACL_FAILED:
            net_mqtt_send_acl_updated(MQTT_ACL_FAIL);
            break;

          case NET_CMD_SEND_WIFI_STR:
            net_mqtt_send_wifi_strength();
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







/*
#ifdef MBEDTLS_DEBUG_C
#define MBEDTLS_DEBUG_LEVEL 4

// mbedtls debug function that translates mbedTLS debug output
//  to ESP_LOGx debug output.
//   MBEDTLS_DEBUG_LEVEL 4 means all mbedTLS debug output gets sent here,
//   and then filtered to the ESP logging mechanism.

static void mbedtls_debug(void *ctx, int level, const char *file, int line, const char *str)
{
    const char *MBTAG = "mbedtls";
    char *file_sep;

    // Shorten 'file' from the whole file path to just the filename
    // This is a bit wasteful because the macros are compiled in with
    // the full _FILE_ path in each case.

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
*/
