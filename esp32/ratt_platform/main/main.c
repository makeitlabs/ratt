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

#include "sdcard.h"
#include "rfid_task.h"
#include "net_task.h"
#include "audio_task.h"
#include "lcd_st7735.h"
#include "FreeSans12pt7b.h"
#include "FreeSans9pt7b.h"

static const char *TAG = "main";


void app_main()
{
    ESP_LOGI(TAG, "in RATT app_main()");
    
    nvs_flash_init();

    sdcard_init();

    rfid_init();
    xTaskCreate(rfid_task, "rfid_task", 2048, NULL, 6, NULL);

    lcd_init();

    //net_init();
    //xTaskCreate(&net_task, "net_task", 8192, NULL, 5, NULL);

    //audio_init();
    //xTaskCreate(&audio_task, "audio_task", 2048, NULL, 10, NULL);


    lcd_fill_screen(lcd_rgb565(0x00, 0x00, 0xF8));

    gfx_draw_circle(64, 80, 32, lcd_rgb565(0xF8, 0xFC, 0x00));

    gfx_set_text_wrap(1);
    gfx_set_text_size(1);
    gfx_set_font(&FreeSans12pt7b);
    gfx_set_text_color(lcd_rgb565(0x00, 0xE0, 0xF8));
    gfx_write_string(0, 20, "Hello World");
    gfx_set_font(&FreeSans9pt7b);
    gfx_set_text_color(lcd_rgb565(0xE0, 0x00, 0x00));
    gfx_write_string(0, 40, "MakeIt Labs");
    
}
