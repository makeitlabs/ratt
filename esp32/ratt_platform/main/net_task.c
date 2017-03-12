#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "freertos/heap_regions.h"
#include "esp_heap_alloc_caps.h"
#include "esp_wifi.h"
#include "esp_event_loop.h"
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

static const char *TAG = "net_task";


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


void net_timer(TimerHandle_t xTimer)
{
    wifi_ap_record_t wifidata;
    if (esp_wifi_sta_get_ap_info(&wifidata)==0){
        display_wifi_rssi(wifidata.rssi);
    }
}

void net_init(void)
{
    char s[32];
    
    ESP_LOGI(TAG, "Initializing network...");

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

    TimerHandle_t timer = xTimerCreate("rssi_timer", (250 / portTICK_PERIOD_MS), pdTRUE, (void*) 0, net_timer);

    if (xTimerStart(timer, 0) != pdPASS) {
        ESP_LOGE(TAG, "Could not start net timer");
    }
}


#define RESP_BUF_SIZE 1024

void net_task(void *pvParameters)
{
    char web_url[128];
    int ret;
    char *resp_buf;
    char s[32];

    vTaskDelay(5000 / portTICK_PERIOD_MS);
    
    net_init();
    

    ESP_LOGI(TAG, "start net task");
    
    snprintf(web_url, sizeof(web_url), "https://%s/%s", WEB_SERVER, WEB_URL_PATH);

    
    while(1) {
        display_net_msg("WIFI WAITING");

        // Wait for the callback to set the CONNECTED_BIT in the event group.
        xEventGroupWaitBits(wifi_event_group, CONNECTED_BIT, false, true, portMAX_DELAY);
        ESP_LOGI(TAG, "Connected to AP...");

        
        display_net_msg("WIFI CONNECT");
        
        ESP_LOGI(TAG, "Free heap size before malloc = %zu", xPortGetFreeHeapSizeCaps(MALLOC_CAP_8BIT));
        
        resp_buf = pvPortMallocCaps(RESP_BUF_SIZE, MALLOC_CAP_8BIT);

        ESP_LOGI(TAG, "Free heap size after malloc = %zu", xPortGetFreeHeapSizeCaps(MALLOC_CAP_8BIT));
        
        if (resp_buf) {
            ESP_LOGI(TAG, "response buffer size = %zu", RESP_BUF_SIZE);

            ret = http_init(0);

            display_net_msg("WIFI DOWNLOAD");

            xSemaphoreTake(g_sdcard_mutex, portMAX_DELAY);
            FILE* file = fopen("/sdcard/acl-temp.txt", "w");
            
            if (file) {
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

            vPortFreeTagged(resp_buf);
            ESP_LOGI(TAG, "Free heap size after free = %zu", xPortGetFreeHeapSizeCaps(MALLOC_CAP_8BIT));
        } else {
            ESP_LOGE(TAG, "Could not malloc acl buffer");
        }
        
        for(int countdown = 120; countdown >= 0; countdown--) {
            vTaskDelay(1000 / portTICK_PERIOD_MS);
            snprintf(s, sizeof(s), "WIFI SLEEP %d", countdown);
            display_net_msg(s);

        }
        ESP_LOGI(TAG, "Starting again!");
    }
}
