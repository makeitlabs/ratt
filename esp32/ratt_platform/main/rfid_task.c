
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "esp_log.h"
#include "esp_system.h"

#include "driver/uart.h"
#include "soc/uart_struct.h"

#define SER_BUF_SIZE (256)
#define SER_RFID_TXD  (17)
#define SER_RFID_RXD  (16)
#define SER_RFID_RTS  (18)
#define SER_RFID_CTS  (19)

static int uart_num = UART_NUM_1;

static const char *TAG = "rfid_task";

void rfid_init()
{
    uart_config_t uart_config = {
        .baud_rate = 9600,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .rx_flow_ctrl_thresh = 122,
    };

    uart_param_config(uart_num, &uart_config);
    uart_set_pin(uart_num, SER_RFID_TXD, SER_RFID_RXD, SER_RFID_RTS, SER_RFID_CTS);
    uart_driver_install(uart_num, SER_BUF_SIZE * 2, 0, 0, NULL, 0);
}

void rfid_task(void *pvParameters)
{

    uint8_t* rxbuf = (uint8_t*) malloc(SER_BUF_SIZE);
    while(1) {
        int len = uart_read_bytes(uart_num, rxbuf, SER_BUF_SIZE, 20 / portTICK_RATE_MS);

        if (len) {
            for (int i=0; i<len; i++) {
                char s[10];
                snprintf(s, sizeof(s), "%2.2X ", rxbuf[i]);
                ESP_LOGI(TAG, "SERIAL RX: %s", s);
                
            }
        }
    }
}

