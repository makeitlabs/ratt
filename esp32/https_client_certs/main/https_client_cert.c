/* HTTPS GET Example using plain mbedTLS sockets
 * with 2-way authentication and encryption using client certificates.
 *
 * Contacts the a configurable URL via TLS v1.2 and reads a response.
 *
 * Adapted from the "04_https_request" example in esp-idf.
 * Now includes my ESP port of HISONA's HTTP/HTTPS REST client C library, which has been tweaked for
 * ESP32 platform stuff, extended to support client certificates, and http basic auth
 *
 * Steve Richardson - steve.richardson@makeitlabs.com
 *
 * Original Copyright (C) 2006-2016, ARM Limited, All Rights Reserved, Apache 2.0 License.
 * Additions Copyright (C) Copyright 2015-2016 Espressif Systems (Shanghai) PTE LTD, Apache 2.0 License.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "freertos/heap_regions.h"
#include "esp_heap_alloc_caps.h"
#include "esp_wifi.h"
#include "esp_event_loop.h"
#include "esp_log.h"
#include "esp_system.h"
#include "nvs_flash.h"
#include "https.h"

#include "lwip/err.h"
#include "lwip/sockets.h"
#include "lwip/sys.h"
#include "lwip/netdb.h"
#include "lwip/dns.h"

#include "mbedtls/platform.h"
#include "mbedtls/net.h"
#include "mbedtls/debug.h"
#include "mbedtls/ssl.h"
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/error.h"
#include "mbedtls/certs.h"
#include "mbedtls/base64.h"

#define SD_CARD

#ifdef SD_CARD
#include "esp_vfs_fat.h"
#include "driver/sdmmc_host.h"
#include "driver/sdmmc_defs.h"
#include "sdmmc_cmd.h"
#endif

// The examples use simple configurations that you can set via 'make menuconfig'.
#define EXAMPLE_WIFI_SSID CONFIG_WIFI_SSID
#define EXAMPLE_WIFI_PASS CONFIG_WIFI_PASSWORD
#define WEB_SERVER CONFIG_WEB_SERVER
#define WEB_PORT CONFIG_WEB_PORT
#define WEB_URL_PATH CONFIG_WEB_URL_PATH
#define WEB_BASIC_AUTH_USER CONFIG_WEB_BASIC_AUTH_USER
#define WEB_BASIC_AUTH_PASS CONFIG_WEB_BASIC_AUTH_PASS

static const char *TAG = "https_example";


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
static void mbedtls_debug(void *ctx, int level,
                     const char *file, int line,
                     const char *str)
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
    switch(event->event_id) {
    case SYSTEM_EVENT_STA_START:
        esp_wifi_connect();
        break;
    case SYSTEM_EVENT_STA_GOT_IP:
        xEventGroupSetBits(wifi_event_group, CONNECTED_BIT);
        break;
    case SYSTEM_EVENT_STA_DISCONNECTED:
        /* This is a workaround as ESP32 WiFi libs don't currently
           auto-reassociate. */
        esp_wifi_connect();
        xEventGroupClearBits(wifi_event_group, CONNECTED_BIT);
        break;
    default:
        break;
    }
    return ESP_OK;
}

static void initialize_wifi(void)
{
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
    ESP_LOGI(TAG, "Setting WiFi configuration SSID %s...", wifi_config.sta.ssid);
    ESP_ERROR_CHECK( esp_wifi_set_mode(WIFI_MODE_STA) );
    ESP_ERROR_CHECK( esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_config) );
    ESP_ERROR_CHECK( esp_wifi_start() );
}

#ifdef SD_CARD
static void initialize_sdcard(void)
{
    ESP_LOGI(TAG, "Initializing SD card");

    sdmmc_host_t host = SDMMC_HOST_DEFAULT();

    // To use 1-line SD mode, uncomment the following line:
    host.flags = SDMMC_HOST_FLAG_1BIT;

    // This initializes the slot without card detect (CD) and write protect (WP) signals.
    // Modify slot_config.gpio_cd and slot_config.gpio_wp if your board has these signals.
    sdmmc_slot_config_t slot_config = SDMMC_SLOT_CONFIG_DEFAULT();

    // Options for mounting the filesystem.
    // If format_if_mount_failed is set to true, SD card will be partitioned and formatted
    // in case when mounting fails.
    esp_vfs_fat_sdmmc_mount_config_t mount_config = {
        .format_if_mount_failed = false,
        .max_files = 5
    };

    // Use settings defined above to initialize SD card and mount FAT filesystem.
    // Note: esp_vfs_fat_sdmmc_mount is an all-in-one convenience function.
    // Please check its source code and implement error recovery when developing
    // production applications.
    sdmmc_card_t* card;
    esp_err_t ret = esp_vfs_fat_sdmmc_mount("/sdcard", &host, &slot_config, &mount_config, &card);
    if (ret != ESP_OK) {
        if (ret == ESP_FAIL) {
            ESP_LOGE(TAG, "Failed to mount filesystem. If you want the card to be formatted, set format_if_mount_failed = true.");
        } else {
            ESP_LOGE(TAG, "Failed to initialize the card (%d). Make sure SD card lines have pull-up resistors in place.", ret);
        }
        return;
    }

    // Card has been initialized, print its properties
    sdmmc_card_print_info(stdout, card);
}
#endif


#define ACL_BUF_SIZE (80 * 1024)

static void https_get_task(void *pvParameters)
{
    char web_url[128];
    int ret;
    char *acl_buf;
    
    snprintf(web_url, sizeof(web_url), "https://%s/%s", WEB_SERVER, WEB_URL_PATH);

    while(1) {
        // Wait for the callback to set the CONNECTED_BIT in the event group.
        xEventGroupWaitBits(wifi_event_group, CONNECTED_BIT,false, true, portMAX_DELAY);
        ESP_LOGI(TAG, "Connected to AP...");

        ESP_LOGI(TAG, "Free heap size before malloc = %zu", xPortGetFreeHeapSizeCaps(MALLOC_CAP_8BIT));
        
        acl_buf = pvPortMallocCaps(ACL_BUF_SIZE, MALLOC_CAP_8BIT);

        ESP_LOGI(TAG, "Free heap size after malloc = %zu", xPortGetFreeHeapSizeCaps(MALLOC_CAP_8BIT));
        
        if (acl_buf) {
            ESP_LOGI(TAG, "ACL buffer size = %zu", ACL_BUF_SIZE);
            
            http_init(0);
            ret = http_get(0, web_url, WEB_BASIC_AUTH_USER, WEB_BASIC_AUTH_PASS, acl_buf, ACL_BUF_SIZE);

#ifdef SD_CARD
            // Use POSIX and C standard library functions to work with files.
            ESP_LOGI(TAG, "Opening file on SD card for write...");
            FILE* f = fopen("/sdcard/acl.txt", "w");
            if (f == NULL) {
                ESP_LOGE(TAG, "Failed to open file for writing...");
                return;
            }
            ret = fwrite(acl_buf, strlen(acl_buf), 1, f);
            if (ret != 1) {
                ESP_LOGE(TAG, "Failed to write to SD card... %d", ret);
            }
            fclose(f);
            ESP_LOGI(TAG, "ACL file written to SD card...");

            // Open file for reading
            ESP_LOGI(TAG, "Reading ACL file from SD card...");
            f = fopen("/sdcard/acl.txt", "r");
            if (f == NULL) {
                ESP_LOGE(TAG, "Failed to open file for reading");
                return;
            }

            char line[128];
            while (fgets(line, sizeof(line), f) == line) {
                ESP_LOGI(TAG, "%s", line);
            }
            fclose(f);

            // All done, unmount partition and disable SDMMC host peripheral
            /*
              esp_vfs_fat_sdmmc_unmount();
              ESP_LOGI(TAG, "Card unmounted");
            */
            
#else
            ESP_LOGI(TAG, "http_get return code: %d", ret);
            for(int i = 0; i < ACL_BUF_SIZE && acl_buf[i] != 0; i++) {
                putchar(acl_buf[i]);
            }
#endif
            
            vPortFreeTagged(acl_buf);
            ESP_LOGI(TAG, "Free heap size after free = %zu", xPortGetFreeHeapSizeCaps(MALLOC_CAP_8BIT));
        } else {
            ESP_LOGE(TAG, "Could not malloc acl buffer");
        }
        

        
        for(int countdown = 5; countdown >= 0; countdown--) {
            ESP_LOGI(TAG, "%d...", countdown);
            vTaskDelay(1000 / portTICK_PERIOD_MS);
        }
        ESP_LOGI(TAG, "Starting again!");
    }
}

void app_main()
{
    nvs_flash_init();
#ifdef SD_CARD
    initialize_sdcard();
#endif
    initialize_wifi();
    xTaskCreate(&https_get_task, "https_get_task", 8192, NULL, 5, NULL);
}
