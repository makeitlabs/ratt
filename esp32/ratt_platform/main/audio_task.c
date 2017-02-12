#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_system.h"
#include "driver/i2s.h"
#include "esp_log.h"
#include "sdcard.h"

static const char *TAG = "audio_task";

#define SAMPLE_RATE     (16000)
#define I2S_NUM         (0)

static QueueHandle_t m_qhandle;

static char buf[512];

void audio_init()
{
    i2s_config_t i2s_config = {
        .mode = I2S_MODE_MASTER | I2S_MODE_TX,
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = 16,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = I2S_COMM_FORMAT_I2S | I2S_COMM_FORMAT_I2S_MSB,
        .dma_buf_count = 8,
        .dma_buf_len = 512,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1
    };
    i2s_pin_config_t pin_config = {
        .bck_io_num = 26,
        .ws_io_num = 25,
        .data_out_num = 22,
        .data_in_num = -1
    };

    i2s_driver_install(I2S_NUM, &i2s_config, 64, &m_qhandle);
    i2s_set_pin(I2S_NUM, &pin_config);    
}



void audio_task(void *pvParameters)
{
    i2s_event_type_t evt;


    ESP_LOGI(TAG, "taking sdcard mutex...");
    xSemaphoreTake(g_sdcard_mutex, portMAX_DELAY);
    
    FILE* f = fopen("/sdcard/smb.s16", "r");

    xSemaphoreGive(g_sdcard_mutex);
    ESP_LOGI(TAG, "gave sdcard mutex...");
    
    while (1) {
        int r;
        do {
            xSemaphoreTake(g_sdcard_mutex, portMAX_DELAY);
            fread(buf, sizeof(buf), 1, f);
            xSemaphoreGive(g_sdcard_mutex);
            
            r = i2s_write_bytes(I2S_NUM, buf, sizeof(buf), portMAX_DELAY);
        } while (r>0);

        if (xQueueReceive(m_qhandle, &evt, 0) == pdTRUE) {
            switch (evt) {
            case I2S_EVENT_DMA_ERROR:
                ESP_LOGE(TAG, "I2S_EVENT_DMA_ERROR");
                break;
            case I2S_EVENT_TX_DONE:
                ESP_LOGI(TAG, "I2S_EVENT_TX_DONE");
                break;
            case I2S_EVENT_RX_DONE:
                ESP_LOGI(TAG, "I2S_EVENT_RX_DONE");
                break;
            default:
                ESP_LOGE(TAG, "I2S ERR unknown event");
            }
        }
    }    
}
