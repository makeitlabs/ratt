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

static const char *TAG = "net_https";

#define WEB_SERVER CONFIG_WEB_SERVER
#define WEB_PORT CONFIG_WEB_PORT
#define WEB_URL_PATH CONFIG_WEB_URL_PATH
#define WEB_BASIC_AUTH_USER CONFIG_WEB_BASIC_AUTH_USER
#define WEB_BASIC_AUTH_PASS CONFIG_WEB_BASIC_AUTH_PASS

#define RESP_BUF_SIZE 1024

int net_https_init(void)
{
  ESP_LOGI(TAG, "net_https init");

  return 0;
}

int net_https_download_acl()
{
  int ret = -1, r;
  char web_url[256];
  char *resp_buf;

  resp_buf = malloc(RESP_BUF_SIZE);
  if (resp_buf) {
      r = http_init(0);
      snprintf(web_url, sizeof(web_url), "https://%s/%s", WEB_SERVER, WEB_URL_PATH);

      display_net_msg("WIFI DOWNLOAD");

      xSemaphoreTake(g_sdcard_mutex, portMAX_DELAY);
      FILE* file = fopen("/sdcard/acl-temp.txt", "w");

      if (file) {
          ESP_LOGI(TAG, "URL: %s", web_url);
          r = http_get(0, web_url, WEB_BASIC_AUTH_USER, WEB_BASIC_AUTH_PASS, resp_buf, RESP_BUF_SIZE, file);

          ESP_LOGI(TAG, "http_get returned %d", r);
          if (r == -1) {
              ESP_LOGE(TAG, "http_get returned -1 (%s)", resp_buf);
              xSemaphoreGive(g_sdcard_mutex);
              goto failed;
          }
          fclose(file);
      } else {
          ESP_LOGE(TAG, "could not open file for writing");
          xSemaphoreGive(g_sdcard_mutex);
          goto failed;
      }
      http_close(0);

      if (r == 200) {
          xSemaphoreTake(g_acl_mutex, portMAX_DELAY);
          // delete existing ACL file if it exists
          struct stat st;
          if (stat("/sdcard/acl.txt", &st) == 0) {
              if (unlink("/sdcard/acl.txt") != 0) {
                ESP_LOGE(TAG, "could not delete old acl file");
                xSemaphoreGive(g_sdcard_mutex);
                xSemaphoreGive(g_acl_mutex);
                goto failed;
              }
          }

          // move downloaded ACL in place
          if (rename("/sdcard/acl-temp.txt", "/sdcard/acl.txt") != 0) {
              ESP_LOGE(TAG, "Could not rename downloaded ACL file!");
              xSemaphoreGive(g_sdcard_mutex);
              xSemaphoreGive(g_acl_mutex);
              goto failed;
          }
          xSemaphoreGive(g_acl_mutex);

          display_net_msg("DOWNLOAD OK");
          net_cmd_queue(NET_CMD_SEND_ACL_UPDATED);
      } else {
        ESP_LOGE(TAG, "http result code != 200");
        xSemaphoreGive(g_sdcard_mutex);
        goto failed;
      }

      xSemaphoreGive(g_sdcard_mutex);

  } else {
      ESP_LOGE(TAG, "Could not malloc acl buffer");
      return -100;
  }

  ESP_LOGI(TAG, "download ACL success!");
  free(resp_buf);
  return 0;

failed:
  free(resp_buf);
  display_net_msg("DOWNLOAD FAIL");
  net_cmd_queue(NET_CMD_SEND_ACL_FAILED);
  return ret;
}
