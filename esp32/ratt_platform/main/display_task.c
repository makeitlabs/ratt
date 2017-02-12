#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_system.h"
#include "esp_log.h"
#include "lcd_st7735.h"
#include "FreeSans9pt7b.h"

static const char *TAG = "display_task";


void mydelay(int ms)
{
    TickType_t delay = ms / portTICK_PERIOD_MS;
    vTaskDelay(delay);
}

void display_task(void *pvParameters)
{
    lcd_init();
    
    while(1) {

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
    }
}

