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

#include <stdio.h>
#include <string.h>
#include <sys/time.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "driver/gpio.h"
#include "esp_system.h"
#include "esp_log.h"
#include "lcd_st7735.h"
#include "FontAtari8.h"

static const char *TAG = "display_task";

#define DISPLAY_QUEUE_DEPTH 8
#define DISPLAY_EVT_BUF_SIZE 32


#define SPIN_LENGTH 4
static char *m_spin[] = { "\x03", "\x09", " ", "\x09" };

typedef enum {
    DISP_CMD_WIFI_MSG = 0x00,
    DISP_CMD_WIFI_RSSI,
    DISP_CMD_NET_MSG,
    DISP_CMD_ALLOWED_MSG,
    DISP_CMD_USER_MSG
} display_cmd_t;

typedef struct display_evt {
    display_cmd_t cmd;
    char buf[DISPLAY_EVT_BUF_SIZE];
    union {
        int16_t rssi;
        uint8_t allowed;
    } params;
} display_evt_t;

static QueueHandle_t m_q;


BaseType_t display_wifi_msg(char *msg)
{
    display_evt_t evt;
    evt.cmd = DISP_CMD_WIFI_MSG;
    strncpy(evt.buf, msg, DISPLAY_EVT_BUF_SIZE);

    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}

BaseType_t display_wifi_rssi(int16_t rssi)
{
    display_evt_t evt;
    evt.cmd = DISP_CMD_WIFI_RSSI;
    evt.params.rssi = rssi;
    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}

BaseType_t display_net_msg(char *msg)
{
    display_evt_t evt;
    evt.cmd = DISP_CMD_NET_MSG;
    strncpy(evt.buf, msg, DISPLAY_EVT_BUF_SIZE);

    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}

BaseType_t display_user_msg(char *msg)
{
    display_evt_t evt;
    evt.cmd = DISP_CMD_USER_MSG;
    strncpy(evt.buf, msg, DISPLAY_EVT_BUF_SIZE);

    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}

BaseType_t display_allowed_msg(char *msg, uint8_t allowed)
{
    display_evt_t evt;
    evt.cmd = DISP_CMD_ALLOWED_MSG;
    strncpy(evt.buf, msg, DISPLAY_EVT_BUF_SIZE);
    evt.params.allowed = allowed;

    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}




void display_init()
{
    gpio_set_direction(GPIO_NUM_36, GPIO_MODE_INPUT);
    gpio_set_direction(GPIO_NUM_37, GPIO_MODE_INPUT);
    gpio_set_direction(GPIO_NUM_38, GPIO_MODE_INPUT);
    gpio_set_direction(GPIO_NUM_39, GPIO_MODE_INPUT);

    m_q = xQueueCreate(DISPLAY_QUEUE_DEPTH, sizeof(display_evt_t));
    if (m_q == NULL) {
        ESP_LOGE(TAG, "FATAL: Cannot create display queue!");
    }

}

void display_task(void *pvParameters)
{
    uint8_t spin_idx = 0;
    char s[32];
    portTickType last_heartbeat_tick;

    last_heartbeat_tick = xTaskGetTickCount();

    lcd_init();
    lcd_fill_screen(lcd_rgb(0x00, 0x00, 0xC0));
    lcd_fill_rect(0, 0, 160, 16, lcd_rgb(0xFF, 0xFF, 0xFF));
    lcd_fill_rect(0, 17, 160, 1, lcd_rgb(0x00, 0x00, 0x00));

    lcd_fill_rect(0, 63, 160, 1, lcd_rgb(0x00, 0x00, 0x00));
    lcd_fill_rect(0, 64, 160, 16, lcd_rgb(0xFF, 0xFF, 0xFF));

    gfx_set_font(&Atari8);
    gfx_set_text_color(lcd_rgb(0x00, 0x00, 0x00));
    gfx_write_string(0, 64, "RSSI");
    gfx_refresh();

    //int b1=0, b2=0, b3=0, b4=0;
    //int last_b1=0, last_b2=0, last_b3=0, last_b4=0;
    while(1) {
        display_evt_t evt;
/*
        // braindead button test
        b1 = gpio_get_level(GPIO_NUM_36);
        b2 = gpio_get_level(GPIO_NUM_37);
        b3 = gpio_get_level(GPIO_NUM_38);
        b4 = gpio_get_level(GPIO_NUM_39);

        if (b1 != last_b1) {
            ESP_LOGI(TAG, "Button 1 now=%d", b1);
        }

        if (b2 != last_b2) {
            ESP_LOGI(TAG, "Button 2 now=%d", b2);
        }

        if (b3 != last_b3) {
            ESP_LOGI(TAG, "Button 3 now=%d", b3);
        }

        if (b4 != last_b4) {
            ESP_LOGI(TAG, "Button 4 now=%d", b4);
        }

        last_b1 = b1;
        last_b2 = b2;
        last_b3 = b3;
        last_b4 = b4;
        // end button test
*/

        if (xQueueReceive(m_q, &evt, (20 / portTICK_PERIOD_MS)) == pdPASS) {
            switch(evt.cmd) {
            case DISP_CMD_WIFI_MSG:
                gfx_set_font(NULL);
                lcd_fill_rect(0, 0, 160, 8, lcd_rgb(0xFF, 0xFF, 0xFF));
                gfx_set_font(&Atari8);
                gfx_set_text_color(lcd_rgb(0x00, 0x00, 0x00));
                gfx_write_string(0, 0, evt.buf);
                gfx_refresh_rect(0, 0, 128, 8);
                break;
            case DISP_CMD_WIFI_RSSI:
                gfx_set_font(NULL);
                lcd_fill_rect(0, 72, 32, 8, lcd_rgb(0xFF, 0xFF, 0xFF));
                gfx_set_font(&Atari8);
                gfx_set_text_color(lcd_rgb(0x00, 0x00, 0x00));
                snprintf(s, sizeof(s), "%d", evt.params.rssi);
                gfx_write_string(0, 72, s);
                gfx_refresh_rect(0, 72, 32, 8);
                break;
            case DISP_CMD_NET_MSG:
                gfx_set_font(NULL);
                lcd_fill_rect(0, 8, 160, 8, lcd_rgb(0xFF, 0xFF, 0xFF));
                gfx_set_font(&Atari8);
                gfx_set_text_color(lcd_rgb(0x00, 0x00, 0x00));
                gfx_write_string(0, 8, evt.buf);
                gfx_refresh_rect(0, 8, 128, 8);
                break;
            case DISP_CMD_USER_MSG:
                gfx_set_font(NULL);
                lcd_fill_rect(0, 24, 160, 8, lcd_rgb(0x00, 0x00, 0xC0));
                gfx_set_font(&Atari8);
                gfx_set_text_color(lcd_rgb(0xFF, 0xFF, 0xFF));
                gfx_write_string(0, 24, evt.buf);
                gfx_refresh_rect(0, 24, 128, 8);
                break;
            case DISP_CMD_ALLOWED_MSG:
                gfx_set_font(&Atari8);
                lcd_fill_rect(0, 32, 160, 8, lcd_rgb(0x00, 0x00, 0xC0));
                gfx_set_text_color(lcd_rgb(0x99, 0x99, 0x99));
                gfx_write_string(0, 32, evt.buf);

                lcd_fill_rect(0, 40, 160, 20, lcd_rgb(0x00, 0x00, 0xC0));
                if (evt.params.allowed) {
                    gfx_set_text_color(lcd_rgb(0x00, 0xFF, 0x00));
                    gfx_write_string(0, 40, "ALLOWED");
                } else {
                    gfx_set_text_color(lcd_rgb(0xFF, 0x00, 0x00));
                    gfx_write_string(0, 40, "DENIED");
                }
                gfx_refresh_rect(0, 32, 160, 16);

                break;
            }
        }

        portTickType now = xTaskGetTickCount();
        if (now - last_heartbeat_tick >= (500/portTICK_PERIOD_MS)) {
            // heartbeat
            gfx_set_font(NULL);
            gfx_draw_char(152, 72, m_spin[spin_idx][0], lcd_rgb(0xFF, 0x00, 0x00), lcd_rgb(0xFF, 0xFF, 0xFF), 1);
            spin_idx = (spin_idx + 1) % SPIN_LENGTH;
            gfx_refresh_rect(152, 72, 6, 8);

            char strftime_buf[64];
            time_t tnow;
            struct tm timeinfo;

            time(&tnow);
            setenv("TZ", "EST5EDT,M3.2.0/2,M11.1.0", 1);
            tzset();
            localtime_r(&tnow, &timeinfo);
            strftime(strftime_buf, sizeof(strftime_buf), "%c", &timeinfo);

            lcd_fill_rect(0, 52, 160, 10, lcd_rgb(0x00, 0x00, 0xC0));
            gfx_set_text_color(lcd_rgb(0xFF, 0xFF, 0x00));
            gfx_write_string(0, 52, strftime_buf);
            gfx_refresh_rect(0, 52, 160, 16);

            last_heartbeat_tick = now;
        }


        /*
        ESP_LOGI(TAG, "Loading image from SD card...");
        gfx_load_rgb565_bitmap(0, 0, 128, 160, "/sdcard/rat.raw");

        mydelay(100);

        ESP_LOGI(TAG, "Drawing graphics & text from primitives...");

        lcd_fill_screen(lcd_rgb(0x00, 0x00, 0xF8));
        gfx_draw_circle(64, 80, 32, lcd_rgb(0xF8, 0xFC, 0x00));
        gfx_draw_circle(64, 80, 24, lcd_rgb(0x00, 0xFC, 0xF8));
        gfx_draw_circle(64, 80, 16, lcd_rgb(0xF8, 0xFC, 0x00));
        gfx_draw_circle(64, 80, 8, lcd_rgb(0x00, 0xFC, 0xF8));

        gfx_set_font(&FreeSans9pt7b);
        gfx_set_text_color(lcd_rgb(0x00, 0xE0, 0xF8));
        gfx_write_string(0, 20, "Hello World");

        gfx_set_font(NULL);
        gfx_set_text_color(lcd_rgb(0x00, 0xFC, 0x00));
        gfx_write_string(0, 22, "from the ESP32!");

        gfx_set_font(&FreeSans9pt7b);
        gfx_set_text_color(lcd_rgb(0xF8, 0xFC, 0xF8));
        gfx_write_string(0, 154, "MakeIt Labs");

        mydelay(100);
        */
    }
}

/*
void mydelay(int ms)
{
    TickType_t delay = ms / portTICK_PERIOD_MS;
    vTaskDelay(delay);
}
*/
