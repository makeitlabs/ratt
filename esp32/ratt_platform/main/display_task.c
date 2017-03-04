#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_system.h"
#include "esp_log.h"
#include "lcd_st7735.h"
#include "FreeSans9pt7b.h"

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
    strncpy(evt.buf, msg, sizeof(evt.buf)-1);

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
    strncpy(evt.buf, msg, sizeof(evt.buf)-1);

    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}

BaseType_t display_user_msg(char *msg)
{
    display_evt_t evt;
    evt.cmd = DISP_CMD_USER_MSG;
    strncpy(evt.buf, msg, sizeof(evt.buf)-1);

    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}

BaseType_t display_allowed_msg(char *msg, uint8_t allowed)
{
    display_evt_t evt;
    evt.cmd = DISP_CMD_ALLOWED_MSG;
    strncpy(evt.buf, msg, sizeof(evt.buf)-1);
    evt.params.allowed = allowed;
    
    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}


void display_init()
{
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
    lcd_fill_screen(lcd_rgb565(0x00, 0x00, 0xC0));

    gfx_set_text_color(lcd_rgb565(0xFF, 0xFF, 0xFF));
    gfx_write_string(0, 144, "RSSI");

    
    while(1) {
        display_evt_t evt;
        
        if (xQueueReceive(m_q, &evt, (100 / portTICK_PERIOD_MS)) == pdPASS) {
            // event received
            ESP_LOGI(TAG, "evt received");

            switch(evt.cmd) {
            case DISP_CMD_WIFI_MSG:
                gfx_set_font(NULL);
                lcd_fill_rect(0, 0, 128, 8, lcd_rgb565(0x00, 0x00, 0xC0));
                gfx_set_text_color(lcd_rgb565(0x00, 0xE0, 0xF8));
                gfx_write_string(0, 0, evt.buf);
                break;
            case DISP_CMD_WIFI_RSSI:
                gfx_set_font(NULL);
                lcd_fill_rect(0, 152, 32, 8, lcd_rgb565(0x00, 0x00, 0xC0));
                gfx_set_text_color(lcd_rgb565(0xFF, 0xFF, 0xFF));
                snprintf(s, sizeof(s), "%d", evt.params.rssi); 
                gfx_write_string(0, 152, s);
                break;
            case DISP_CMD_NET_MSG:
                gfx_set_font(NULL);
                lcd_fill_rect(0, 8, 128, 8, lcd_rgb565(0x00, 0x00, 0xC0));
                gfx_set_text_color(lcd_rgb565(0xF8, 0xE0, 0x00));
                gfx_write_string(0, 8, evt.buf);
                break;
            case DISP_CMD_USER_MSG:
                gfx_set_font(NULL);
                lcd_fill_rect(0, 24, 128, 8, lcd_rgb565(0x00, 0x00, 0xC0));
                gfx_set_text_color(lcd_rgb565(0xFF, 0xFF, 0xFF));
                gfx_write_string(0, 24, evt.buf);
                break;
            case DISP_CMD_ALLOWED_MSG:
                gfx_set_font(NULL);
                lcd_fill_rect(0, 32, 128, 8, lcd_rgb565(0x00, 0x00, 0xC0));
                if (evt.params.allowed) {
                    gfx_set_text_color(lcd_rgb565(0x00, 0xFF, 0x00));
                } else {
                    gfx_set_text_color(lcd_rgb565(0xFF, 0x00, 0x00));
                }
                gfx_write_string(0, 32, evt.buf);
                break;
            }
            
        }

        portTickType now = xTaskGetTickCount();
        if (now - last_heartbeat_tick >= (500/portTICK_PERIOD_MS)) {
            // heartbeat
            gfx_set_font(NULL);
            gfx_draw_char(122, 152, m_spin[spin_idx][0], lcd_rgb565(0x00, 0xFC, 0x00), lcd_rgb565(0x00, 0x00, 0xC0), 1);
            spin_idx = (spin_idx + 1) % SPIN_LENGTH;

            last_heartbeat_tick = now;
        }

        
        /*
        ESP_LOGI(TAG, "Loading image from SD card...");
        gfx_load_rgb565_bitmap(0, 0, 128, 160, "/sdcard/rat.raw");

        mydelay(100);
        
        ESP_LOGI(TAG, "Drawing graphics & text from primitives...");
        
        lcd_fill_screen(lcd_rgb565(0x00, 0x00, 0xF8));
        gfx_draw_circle(64, 80, 32, lcd_rgb565(0xF8, 0xFC, 0x00));
        gfx_draw_circle(64, 80, 24, lcd_rgb565(0x00, 0xFC, 0xF8));
        gfx_draw_circle(64, 80, 16, lcd_rgb565(0xF8, 0xFC, 0x00));
        gfx_draw_circle(64, 80, 8, lcd_rgb565(0x00, 0xFC, 0xF8));
        
        gfx_set_font(&FreeSans9pt7b);
        gfx_set_text_color(lcd_rgb565(0x00, 0xE0, 0xF8));
        gfx_write_string(0, 20, "Hello World");

        gfx_set_font(NULL);
        gfx_set_text_color(lcd_rgb565(0x00, 0xFC, 0x00));
        gfx_write_string(0, 22, "from the ESP32!");
        
        gfx_set_font(&FreeSans9pt7b);
        gfx_set_text_color(lcd_rgb565(0xF8, 0xFC, 0xF8));
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
