/* HTTPS GET Example using plain mbedTLS sockets
 * with 2-way authentication and encryption using client certificates.
 *
 * Contacts the a configurable URL via TLS v1.2 and reads a response.
 *
 * Adapted from the "04_https_request" example in esp-idf.
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
#include "esp_wifi.h"
#include "esp_event_loop.h"
#include "esp_log.h"
#include "esp_system.h"
#include "nvs_flash.h"

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

// The examples use simple configurations that you can set via 'make menuconfig'.
#define EXAMPLE_WIFI_SSID CONFIG_WIFI_SSID
#define EXAMPLE_WIFI_PASS CONFIG_WIFI_PASSWORD
#define WEB_SERVER CONFIG_WEB_SERVER
#define WEB_PORT CONFIG_WEB_PORT
#define WEB_URL_PATH CONFIG_WEB_URL_PATH
#define WEB_BASIC_AUTH_USER CONFIG_WEB_BASIC_AUTH_USER
#define WEB_BASIC_AUTH_PASS CONFIG_WEB_BASIC_AUTH_PASS

#define CLIENT_PK_PASSPHRASE CONFIG_CLIENT_PK_PASSPHRASE

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

static void initialise_wifi(void)
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

static void https_get_task(void *pvParameters)
{
    char web_url[128];
    char request[256];
    
    char buf[512];
    int ret, flags, len;

    mbedtls_entropy_context entropy;
    mbedtls_ctr_drbg_context ctr_drbg;
    mbedtls_ssl_context ssl;

    extern const uint8_t ca_cert_pem_start[] asm("_binary_cacert_pem_start");
    extern const uint8_t ca_cert_pem_end[]   asm("_binary_cacert_pem_end");
    
    extern const uint8_t client_cert_pem_start[] asm("_binary_client_cert_pem_start");
    extern const uint8_t client_cert_pem_end[]   asm("_binary_client_cert_pem_end");
    
    extern const uint8_t client_key_pem_start[] asm("_binary_client_key_pem_start");
    extern const uint8_t client_key_pem_end[]   asm("_binary_client_key_pem_end");
    
    mbedtls_x509_crt ca_cert;
    mbedtls_x509_crt client_cert;

    mbedtls_pk_context client_pk;
    char client_pk_passphrase[32];
    
    mbedtls_ssl_config conf;
    mbedtls_net_context server_fd;

    snprintf(web_url, sizeof(web_url), "https://%s/%s", WEB_SERVER, WEB_URL_PATH);

    // build the http request
    if (strcmp(WEB_BASIC_AUTH_USER, "") != 0) {
        size_t olen;
        unsigned char base64[32];
        char auth[64];
        
        snprintf(auth, sizeof(auth), "%s:%s", WEB_BASIC_AUTH_USER, WEB_BASIC_AUTH_PASS);
        if ((ret = mbedtls_base64_encode(base64, 32, &olen, (const unsigned char*)auth, strlen(auth))) != 0) {
            ESP_LOGE(TAG, "mbedtls_base64_encode returned -0x%x\n\n", -ret);
            abort();
        }

        buf[olen] = '\0';
        snprintf(auth, sizeof(auth), "Authorization: Basic %s", base64);

        // basic auth required
        snprintf(request, sizeof(request),
                 "GET %s HTTP/1.1\n"
                 "Host: %s\n"
                 "%s\n"
                 "User-Agent: esp-idf/1.0 esp32\n"
                 "Connection: close\n"
                 "\n", web_url, WEB_SERVER, auth);
    } else {
        // no basic auth required
        snprintf(request, sizeof(request),
                 "GET %s HTTP/1.1\n"
                 "Host: %s\n"
                 "User-Agent: esp-idf/1.0 esp32\n"
                 "Connection: close\n"
                 "\n", web_url, WEB_SERVER);
        
    }

    ESP_LOGI(TAG, "request header:\n%s", request);

    mbedtls_ssl_init(&ssl);
    mbedtls_x509_crt_init(&ca_cert);
    mbedtls_x509_crt_init(&client_cert);
    mbedtls_pk_init(&client_pk);
    
    mbedtls_ctr_drbg_init(&ctr_drbg);
    ESP_LOGI(TAG, "Seeding the random number generator");

    mbedtls_ssl_config_init(&conf);

    mbedtls_entropy_init(&entropy);
    if((ret = mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy, NULL, 0)) != 0)
    {
        ESP_LOGE(TAG, "mbedtls_ctr_drbg_seed returned %d", ret);
        abort();
    }

    ESP_LOGI(TAG, "Loading the CA root certificate...");
    ret = mbedtls_x509_crt_parse(&ca_cert, ca_cert_pem_start, ca_cert_pem_end - ca_cert_pem_start);
    if(ret < 0)
    {
        ESP_LOGE(TAG, "mbedtls_x509_crt_parse returned -0x%x\n\n", -ret);
        abort();
    }

    ESP_LOGI(TAG, "Loading the client certificate...");
    ret = mbedtls_x509_crt_parse(&client_cert, client_cert_pem_start, client_cert_pem_end - client_cert_pem_start);
    if(ret < 0)
    {
        ESP_LOGE(TAG, "mbedtls_x509_crt_parse returned -0x%x\n\n", -ret);
        abort();
    }

    ESP_LOGI(TAG, "Loading the client key...");
    snprintf(client_pk_passphrase, sizeof(client_pk_passphrase) - 1, CLIENT_PK_PASSPHRASE);
    ret = mbedtls_pk_parse_key(&client_pk, client_key_pem_start, client_key_pem_end - client_key_pem_start, (const unsigned char*) client_pk_passphrase, strlen(client_pk_passphrase));
    if(ret < 0)
    {
        ESP_LOGE(TAG, "mbedtls_pk_parse_key returned -0x%x\n\n", -ret);
        abort();
    }
    
    ESP_LOGI(TAG, "Setting hostname for TLS session...");

    // Hostname set here should match CN in server certificate
    if((ret = mbedtls_ssl_set_hostname(&ssl, WEB_SERVER)) != 0)
    {
        ESP_LOGE(TAG, "mbedtls_ssl_set_hostname returned -0x%x", -ret);
        abort();
    }

    ESP_LOGI(TAG, "Setting up the SSL/TLS structure...");

    if((ret = mbedtls_ssl_config_defaults(&conf,
                                          MBEDTLS_SSL_IS_CLIENT,
                                          MBEDTLS_SSL_TRANSPORT_STREAM,
                                          MBEDTLS_SSL_PRESET_DEFAULT)) != 0)
    {
        ESP_LOGE(TAG, "mbedtls_ssl_config_defaults returned %d", ret);
        goto exit;
    }

    // MBEDTLS_SSL_VERIFY_REQUIRED means the CA verification must succeed to connect.
    mbedtls_ssl_conf_authmode(&conf, MBEDTLS_SSL_VERIFY_REQUIRED);

    // set up our own client certificate
    mbedtls_ssl_conf_own_cert(&conf, &client_cert, &client_pk);

    // set up the CA certificate
    mbedtls_ssl_conf_ca_chain(&conf, &ca_cert, NULL);
    
    mbedtls_ssl_conf_rng(&conf, mbedtls_ctr_drbg_random, &ctr_drbg);
#ifdef MBEDTLS_DEBUG_C
    mbedtls_debug_set_threshold(MBEDTLS_DEBUG_LEVEL);
    mbedtls_ssl_conf_dbg(&conf, mbedtls_debug, NULL);
#endif

    if ((ret = mbedtls_ssl_setup(&ssl, &conf)) != 0)
    {
        ESP_LOGE(TAG, "mbedtls_ssl_setup returned -0x%x\n\n", -ret);
        goto exit;
    }

    while(1) {
        // Wait for the callback to set the CONNECTED_BIT in the event group.
        xEventGroupWaitBits(wifi_event_group, CONNECTED_BIT,false, true, portMAX_DELAY);
        ESP_LOGI(TAG, "Connected to AP");

        mbedtls_net_init(&server_fd);

        ESP_LOGI(TAG, "Connecting to %s:%s...", WEB_SERVER, WEB_PORT);

        if ((ret = mbedtls_net_connect(&server_fd, WEB_SERVER, WEB_PORT, MBEDTLS_NET_PROTO_TCP)) != 0)
        {
            ESP_LOGE(TAG, "mbedtls_net_connect returned -%x", -ret);
            goto exit;
        }

        ESP_LOGI(TAG, "Connected.");
        mbedtls_ssl_set_bio(&ssl, &server_fd, mbedtls_net_send, mbedtls_net_recv, NULL);

        ESP_LOGI(TAG, "Performing the SSL/TLS handshake...");
        while ((ret = mbedtls_ssl_handshake(&ssl)) != 0)
        {
            if (ret != MBEDTLS_ERR_SSL_WANT_READ && ret != MBEDTLS_ERR_SSL_WANT_WRITE)
            {
                ESP_LOGE(TAG, "mbedtls_ssl_handshake returned -0x%x", -ret);
                goto exit;
            }
        }

        ESP_LOGI(TAG, "Verifying peer X.509 certificate...");
        if ((flags = mbedtls_ssl_get_verify_result(&ssl)) != 0)
        {
            // TODO: probably want to close connection if ret != 0
            ESP_LOGW(TAG, "Failed to verify peer certificate!");
            bzero(buf, sizeof(buf));
            mbedtls_x509_crt_verify_info(buf, sizeof(buf), "  ! ", flags);
            ESP_LOGW(TAG, "verification info: %s", buf);
        } else {
            ESP_LOGI(TAG, "Certificate verified.");
        }

        ESP_LOGI(TAG, "Writing HTTP request...");

        while((ret = mbedtls_ssl_write(&ssl, (const unsigned char *)request, strlen(request))) <= 0)
        {
            if(ret != MBEDTLS_ERR_SSL_WANT_READ && ret != MBEDTLS_ERR_SSL_WANT_WRITE)
            {
                ESP_LOGE(TAG, "mbedtls_ssl_write returned -0x%x", -ret);
                goto exit;
            }
        }

        len = ret;
        ESP_LOGI(TAG, "%d bytes written", len);
        ESP_LOGI(TAG, "Reading HTTP response...");

        do
        {
            len = sizeof(buf) - 1;
            bzero(buf, sizeof(buf));
            ret = mbedtls_ssl_read(&ssl, (unsigned char *)buf, len);

            if(ret == MBEDTLS_ERR_SSL_WANT_READ || ret == MBEDTLS_ERR_SSL_WANT_WRITE)
                continue;

            if(ret == MBEDTLS_ERR_SSL_PEER_CLOSE_NOTIFY) {
                ret = 0;
                break;
            }

            if(ret < 0)
            {
                ESP_LOGE(TAG, "mbedtls_ssl_read returned -0x%x", -ret);
                break;
            }

            if(ret == 0)
            {
                ESP_LOGI(TAG, "connection closed");
                break;
            }

            len = ret;
            //ESP_LOGI(TAG, "%d bytes read", len);
            for(int i = 0; i < len; i++) {
                putchar(buf[i]);
            }
        } while(1);

        mbedtls_ssl_close_notify(&ssl);

    exit:
        mbedtls_ssl_session_reset(&ssl);
        mbedtls_net_free(&server_fd);

        if(ret != 0)
        {
            mbedtls_strerror(ret, buf, 100);
            ESP_LOGE(TAG, "Last error was: -0x%x - %s", -ret, buf);
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
    initialise_wifi();
    xTaskCreate(&https_get_task, "https_get_task", 8192, NULL, 5, NULL);
}
