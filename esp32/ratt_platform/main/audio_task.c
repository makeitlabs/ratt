#include <stdio.h>
#include <string.h>
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

#define DMA_BUF_SIZE 512
#define DMA_BUF_COUNT 4

static QueueHandle_t m_drv_q;
static char buf[DMA_BUF_SIZE];



typedef enum {
    AUDIO_CMD_PLAY,
    AUDIO_CMD_STOP
} audio_cmd_t;


#define AUDIO_QUEUE_DEPTH 8
#define AUDIO_EVT_BUF_SIZE 32

typedef struct audio_evt {
    audio_cmd_t cmd;
    char buf[AUDIO_EVT_BUF_SIZE];
    char interrupt;
    char repeat;
} audio_evt_t;

static QueueHandle_t m_evt_q;



void audio_init()
{
    i2s_config_t i2s_config = {
        .mode = I2S_MODE_MASTER | I2S_MODE_TX,
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = 16,
        .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT,
        .communication_format = I2S_COMM_FORMAT_I2S | I2S_COMM_FORMAT_I2S_MSB,
        .dma_buf_count = DMA_BUF_COUNT,
        .dma_buf_len = DMA_BUF_SIZE,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1
    };
    i2s_pin_config_t pin_config = {
        .bck_io_num = 26,
        .ws_io_num = 25,
        .data_out_num = 17,
        .data_in_num = -1
    };

    i2s_driver_install(I2S_NUM, &i2s_config, 64, &m_drv_q);
    i2s_set_pin(I2S_NUM, &pin_config);    

    //i2s_stop(I2S_NUM);
    
    m_evt_q = xQueueCreate(AUDIO_QUEUE_DEPTH, sizeof(audio_evt_t));

    if (m_evt_q == NULL) {
        ESP_LOGE(TAG, "FATAL: Cannot create audio event queue!");
    }

}


BaseType_t audio_play(char *file)
{
    audio_evt_t evt;
    evt.cmd = AUDIO_CMD_PLAY;
    strncpy(evt.buf, file, sizeof(evt.buf)-1);

    return xQueueSendToBack(m_evt_q, &evt, 250 / portTICK_PERIOD_MS);
}

int audio_read(FILE* f)
{
    int r;
    int count = 0;
    int bytes_read = 0;

    if (xSemaphoreTake(g_sdcard_mutex, (10 / portTICK_PERIOD_MS)) != pdTRUE) {
        ESP_LOGE(TAG, "can't get sd mutex!");
        return 0;
    }
    do {
        bytes_read = fread(buf, sizeof(char), DMA_BUF_SIZE, f);
        if (bytes_read > 0 && bytes_read != DMA_BUF_SIZE) {
            bzero(buf + bytes_read, DMA_BUF_SIZE - bytes_read);
        }

        r = i2s_write_bytes(I2S_NUM, buf, DMA_BUF_SIZE, portMAX_DELAY);
        count++;
    } while (!feof(f) && r>0 && count < DMA_BUF_COUNT);

    if (feof(f)) {
        ESP_LOGI(TAG, "file done");
        xSemaphoreGive(g_sdcard_mutex);
        return -1;
    }
    
    xSemaphoreGive(g_sdcard_mutex);
    
    return 1;
}

void audio_task(void *pvParameters)
{
    FILE* f = NULL;
    int count = DMA_BUF_COUNT;
    
    while(1) {
        audio_evt_t evt;
        i2s_event_type_t i2s_evt;

        if (xQueueReceive(m_drv_q, &i2s_evt, (20 / portTICK_PERIOD_MS)) == pdTRUE) {
            switch (i2s_evt) {
            case I2S_EVENT_DMA_ERROR:
                ESP_LOGE(TAG, "I2S_EVENT_DMA_ERROR");
                break;
            case I2S_EVENT_TX_DONE:
                //ESP_LOGI(TAG, "I2S_EVENT_TX_DONE");
                if (f) {
                    if (audio_read(f) == -1) {
                        fclose(f);
                        f = NULL;
                    }
                }

                if (!f) {
                    ESP_LOGI(TAG, "count=%d", count);
                    if (count == 0) {
                        ESP_LOGI(TAG, "stopping I2S");
                        count = DMA_BUF_COUNT;
                        i2s_stop(I2S_NUM);
                    }
                    count--;
                }

                break;
            case I2S_EVENT_RX_DONE:
                ESP_LOGI(TAG, "I2S_EVENT_RX_DONE");
                break;
            default:
                ESP_LOGE(TAG, "I2S ERR unknown event");
            }
        }
        
        if (xQueueReceive(m_evt_q, &evt, (20 / portTICK_PERIOD_MS)) == pdTRUE) {
            // event received
            ESP_LOGI(TAG, "evt received");

            switch(evt.cmd) {
            case AUDIO_CMD_PLAY:
                xSemaphoreTake(g_sdcard_mutex, portMAX_DELAY);
                if (f) {
                    ESP_LOGI(TAG, "closing open file");
                    fclose(f);
                    f = NULL;
                }
                
                ESP_LOGI(TAG, "opening new file %s", evt.buf);
                f = fopen(evt.buf, "r");
                xSemaphoreGive(g_sdcard_mutex);

                i2s_start(I2S_NUM);
                i2s_zero_dma_buffer(I2S_NUM);
                
                break;
            case AUDIO_CMD_STOP:
                xSemaphoreTake(g_sdcard_mutex, portMAX_DELAY);
                if (f) {
                    fclose(f);
                    f = NULL;
                }
                xSemaphoreGive(g_sdcard_mutex);
                break;
            }
        }

    }

    
    while(1);
}
