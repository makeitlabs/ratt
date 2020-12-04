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
#include <stdlib.h>
#include <esp_log.h>
#include <esp_system.h>

#include <driver/uart.h>
#include <soc/uart_struct.h>
#include <mbedtls/sha256.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "beep_task.h"
#include "rfid_task.h"
#include "sdcard.h"
#include "display_task.h"
#include "audio_task.h"

#include "soc/gpio_struct.h"
#include "driver/gpio.h"


#define SER_BUF_SIZE (256)
#define SER_RFID_TXD  (-1)
#define SER_RFID_RXD  (16)
#define SER_RFID_RTS  (-1)
#define SER_RFID_CTS  (-1)

static int uart_num = UART_NUM_1;

static const char *TAG = "rfid_task";

SemaphoreHandle_t g_acl_mutex;

#define MOTOR_O1 (25)
#define MOTOR_O2 (26)


void rfid_init()
{
  gpio_config_t mo1_cfg = {
      .pin_bit_mask = MOTOR_O1,
      .mode = GPIO_MODE_OUTPUT,
      .pull_up_en = GPIO_PULLUP_ENABLE,
      .pull_down_en = GPIO_PULLDOWN_DISABLE,
      .intr_type = GPIO_INTR_DISABLE
  };
  gpio_config_t mo2_cfg = {
      .pin_bit_mask = MOTOR_O2,
      .mode = GPIO_MODE_OUTPUT,
      .pull_up_en = GPIO_PULLUP_ENABLE,
      .pull_down_en = GPIO_PULLDOWN_DISABLE,
      .intr_type = GPIO_INTR_DISABLE
  };


  ESP_LOGI(TAG, "GPIO configuration...");
//  gpio_config(&mo1_cfg);
//  gpio_config(&mo2_cfg);

  gpio_set_direction(MOTOR_O1, GPIO_MODE_OUTPUT);
  gpio_set_direction(MOTOR_O2, GPIO_MODE_OUTPUT);

  gpio_set_level(MOTOR_O1, 1);
  gpio_set_level(MOTOR_O2, 1);


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



    g_acl_mutex = xSemaphoreCreateMutex();
    if (!g_sdcard_mutex) {
        ESP_LOGE(TAG, "Could not create ACL file mutex.");
        return;
    }
}

//
// create a hex digest of the SHA224 hashed tag
// this is some legacy stuff of the MakeIt RFID system where tags are internally saved/managed as SHA224
// not really very useful for security as the entire key space can be hashed and looked up in a few seconds
// but it does prevent the RFID tag IDs from being stored/transferred in the clear
//
void rfid_hash_sha224(char *tag_ascii, int ascii_len, char *tag_hexdigest, int digest_len)
{
    unsigned char tag_sha224[32];

    // set last arg = 1 for SHA224 instead of SHA256
    mbedtls_sha256((unsigned char*)tag_ascii, ascii_len, tag_sha224, 1);

    bzero(tag_hexdigest, digest_len);

    // last 4 bytes of a SHA224 are 0 so ignore them
    for (int i=0; i<28; i++) {
        char s[3];
        snprintf(s, sizeof(s), "%2.2x", tag_sha224[i]);
        strncat(tag_hexdigest, s, digest_len);
    }
}

#define LINE_SIZE 256
uint8_t rfid_lookup(uint32_t tag, user_fields_t *user)
{
    char tag_ascii[32];
    char tag_sha224[65];
    char line[LINE_SIZE];

    snprintf(tag_ascii, sizeof(tag_ascii), "%10.10u", tag);
    rfid_hash_sha224(tag_ascii, strlen(tag_ascii), tag_sha224, sizeof(tag_sha224));

    ESP_LOGI(TAG, "RFID tag: %10.10u", tag);
    ESP_LOGI(TAG, "RFID tag SHA224 hexdigest: %s", tag_sha224);

    // Open file for reading
    ESP_LOGI(TAG, "Reading ACL file from SD card...");

    xSemaphoreTake(g_sdcard_mutex, portMAX_DELAY);
    xSemaphoreTake(g_acl_mutex, portMAX_DELAY);

    FILE *f = fopen("/sdcard/acl.txt", "r");
    if (f == NULL) {
        ESP_LOGE(TAG, "Failed to open ACL file for reading!");
        xSemaphoreGive(g_sdcard_mutex);
        xSemaphoreGive(g_acl_mutex);
        return 0;
    }

    uint8_t found = 0;
    while ((fgets(line, LINE_SIZE, f) != NULL) && !found) {
        //username,key,value,allowed,hashedCard,lastAccessed
        //ESP_LOGI(TAG, "%s", line);

        char *str = line;
        char *token;
        char *fields[10];
        int num_fields;

        num_fields = 0;
        while ((token = strsep(&str, ",")) != NULL && num_fields <= 10) {
            fields[num_fields++] = token;
        }

        if (num_fields == 6) {
            char *username = fields[0];
            //char *key = fields[1];
            //char *value = fields[2];
            char *allowed = fields[3];
            char *hashed_card = fields[4];
            char *last_accessed = fields[5];

            //ESP_LOGI(TAG, "comparing %s to %s", tag_sha224, hashed_card);
            if (strcmp(tag_sha224, hashed_card) == 0) {
                ESP_LOGI(TAG, "found tag for user %s, allowed=%s, last accessed=%s", username, allowed, last_accessed);
                found = 1;

                strncpy(user->name, username, sizeof(user->name));
                strncpy(user->last_accessed, last_accessed, sizeof(user->last_accessed));
                user->allowed = (strcmp(allowed, "allowed") == 0);
            }
        }
    }
    fclose(f);

    xSemaphoreGive(g_acl_mutex);
    xSemaphoreGive(g_sdcard_mutex);

    return found;
}


/*
 * sample packet from "Gwiot 7941e V3.0" eBay RFID module:
 *
 * 00   01   02   03   04   05   06   07   08   09   BYTE #
 * -----------------------------------------------------------
 * 02   0A   02   11   00   0D   EF   80   7B   03
 * |    |    |    |    |    |    |    |    |    |
 * STX  ??   ??   ??   id3  id2  id1  id0  sum  ETX
 *
 * checksum (byte 8, 'sum') is a simple 8-bit XOR of bytes 01 through 07
 * starting the checksum with the value of 'sum' or starting with 0 and
 * including the value of 'sum' in the calculation will net a checksum
 * value of 0 when correct
 *
 * the actual tag value is contained in bytes 04 through 07 as a 32-bit
 * unsigned integer.  byte 04 ('id3') is the most significant byte, while
 * byte 07 ('id0') is the least significant byte.
 */

void rfid_task(void *pvParameters)
{
    uint8_t* rxbuf = (uint8_t*) malloc(SER_BUF_SIZE);

    while(1) {
        int len = uart_read_bytes(uart_num, rxbuf, SER_BUF_SIZE, 20 / portTICK_RATE_MS);

        if (len==10) {

            uint8_t checksum_calc = 0;
            for (uint8_t i=1; i<8; i++) checksum_calc ^= rxbuf[i];

            if (rxbuf[0] == 0x02 && rxbuf[9] == 0x03 && checksum_calc == rxbuf[8]) {
                uint32_t tag = (rxbuf[4]<<24) | (rxbuf[5]<<16) | (rxbuf[6]<<8) | rxbuf[7];

                char s[80];
                ESP_LOGI(TAG, "Good RFID tag checksum, bytes follow:");
                snprintf(s, sizeof(s), "%10.10u %2.2X %2.2X %2.2X %2.2X [%2.2X == %2.2X]", tag, rxbuf[4], rxbuf[5], rxbuf[6], rxbuf[7], rxbuf[8], checksum_calc);
                ESP_LOGI(TAG, "%s", s);

                snprintf(s, sizeof(s), "%10.10u", tag);
                display_user_msg(s);

                beep_queue(880, 250, 5, 5);
                beep_queue(1174, 250, 5, 100);

                display_allowed_msg("OPEN", 1);

                gpio_set_level(MOTOR_O1, 0);
                gpio_set_level(MOTOR_O2, 1);
                display_allowed_msg("HOLD", 1);

                vTaskDelay(500 / portTICK_PERIOD_MS);
                gpio_set_level(MOTOR_O1, 1);
                gpio_set_level(MOTOR_O2, 1);


                vTaskDelay(3000 / portTICK_PERIOD_MS);

                display_allowed_msg("LOCK", 1);
                gpio_set_level(MOTOR_O1, 1);
                gpio_set_level(MOTOR_O2, 0);
                vTaskDelay(500 / portTICK_PERIOD_MS);
                gpio_set_level(MOTOR_O1, 1);
                gpio_set_level(MOTOR_O2, 1);

                beep_queue(1174, 250, 5, 5);
                beep_queue(880, 250, 5, 100);


                /*
                user_fields_t user;
                bzero(&user, sizeof(user));
                if (rfid_lookup(tag, &user)) {
                    display_user_msg(user.name);
                    display_allowed_msg(user.last_accessed, user.allowed);
                    if (user.allowed) {
                        audio_play("/sdcard/granted.s16");
                    } else {
                        audio_play("/sdcard/denied.s16");
                    }
                } else {
                    display_user_msg("Unknown Tag");
                    display_allowed_msg("DENIED", 0);
                    audio_play("/sdcard/denied.s16");
                }
                */

            } else {
                char s[80];
                ESP_LOGI(TAG, "Bad RFID tag checksum, bytes follow:");
                snprintf(s, sizeof(s), "%2.2X %2.2X %2.2X %2.2X [%2.2X != %2.2X]", rxbuf[0], rxbuf[1], rxbuf[2], rxbuf[3], rxbuf[4], checksum_calc);
                ESP_LOGI(TAG, "%s", s);
            }
        }
    }
}
