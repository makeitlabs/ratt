
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <esp_log.h>
#include <esp_system.h>

#include <driver/uart.h>
#include <soc/uart_struct.h>
#include <mbedtls/sha256.h>

#include "display_task.h"

#define SER_BUF_SIZE (256)
#define SER_RFID_TXD  (-1)
#define SER_RFID_RXD  (16)
#define SER_RFID_RTS  (-1)
#define SER_RFID_CTS  (-1)

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

//
// create a hex digest of the hashed tag
// this is some legacy stuff of the MakeIt RFID system where tags are internally saved/managed as SHA224
// not really very useful for security as the entire key space can be hashed and looked up in a few seconds
// but it does prevent the RFID tag IDs from being stored/transferred in the clear
//
void rfid_hash_sha224(char *tag_ascii, int ascii_len, char *tag_hexdigest, int digest_len)
{
    unsigned char tag_sha224[32];

    // last arg = 1 for SHA224 instead of SHA256
    mbedtls_sha256((unsigned char*)tag_ascii, ascii_len, tag_sha224, 1); 
    
    // last 4 bytes of a SHA224 are 0 so ignore them
    bzero(tag_hexdigest, digest_len);
    for (int i=0; i<28; i++) {
        char s[3];
        snprintf(s, sizeof(s), "%2.2x", tag_sha224[i]);
        strncat(tag_hexdigest, s, digest_len);
    }
}

void rfid_task(void *pvParameters)
{
    uint8_t* rxbuf = (uint8_t*) malloc(SER_BUF_SIZE);


    while(1) {
        int len = uart_read_bytes(uart_num, rxbuf, SER_BUF_SIZE, 20 / portTICK_RATE_MS);

        if (len==5) {
            char tag_ascii[32];
            char tag_hexdigest[65];

            uint8_t checksum_calc = rxbuf[0] ^ rxbuf[1] ^ rxbuf[2] ^ rxbuf[3];
            if (checksum_calc == rxbuf[4]) {
                uint32_t tag = (rxbuf[0]<<24) | (rxbuf[1]<<16) | (rxbuf[2]<<8) | rxbuf[3];
                snprintf(tag_ascii, sizeof(tag_ascii), "%10.10u", tag);
                display_rfid_msg(tag_ascii);
                ESP_LOGI(TAG, "Scanned RFID tag %10.10u", tag);
                
                rfid_hash_sha224(tag_ascii, strlen(tag_ascii), tag_hexdigest, sizeof(tag_hexdigest));
                
                ESP_LOGI(TAG, "RFID tag SHA224 hexdigest: %s", tag_hexdigest);
                
            } else {
                char s[80];
                ESP_LOGI(TAG, "Bad RFID tag checksum, bytes follow:");
                snprintf(s, sizeof(s), "%2.2X %2.2X %2.2X %2.2X [%2.2X != %2.2X]", rxbuf[0], rxbuf[1], rxbuf[2], rxbuf[3], rxbuf[4], checksum_calc);
                ESP_LOGI(TAG, "%s", s);
            }
        }
    }
}

