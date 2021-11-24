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
#include "system.h"
#include "system_task.h"

static const char *TAG = "system_task";

#define SYSTEM_QUEUE_DEPTH 8

typedef struct system_evt {
  int cmd;
} system_evt_t;

static QueueHandle_t m_q;


void power_mgmt_init(void)
{
  gpio_reset_pin(GPIO_PIN_SHUTDOWN);
  gpio_set_direction(GPIO_PIN_SHUTDOWN, GPIO_MODE_OUTPUT);
  gpio_set_level(GPIO_PIN_SHUTDOWN, 1);

  gpio_reset_pin(GPIO_PIN_PWR_ENABLE);
  gpio_set_direction(GPIO_PIN_PWR_ENABLE, GPIO_MODE_OUTPUT);
  gpio_set_level(GPIO_PIN_PWR_ENABLE, 1);

  gpio_reset_pin(GPIO_PIN_N_PWR_LOSS);
  gpio_set_direction(GPIO_PIN_N_PWR_LOSS, GPIO_MODE_INPUT);

  gpio_reset_pin(GPIO_PIN_LOW_BAT);
  gpio_set_direction(GPIO_PIN_LOW_BAT, GPIO_MODE_INPUT);
}

void system_init(void)
{
  m_q = xQueueCreate(SYSTEM_QUEUE_DEPTH, sizeof(system_evt_t));
  if (m_q == NULL) {
      ESP_LOGE(TAG, "FATAL: Cannot create system task queue!");
  }

  power_mgmt_init();
}


void sdelay(int ms)
{
    TickType_t delay = ms / portTICK_PERIOD_MS;
    vTaskDelay(delay);
}

void system_task(void *pvParameters)
{
  ESP_LOGI(TAG, "System management task started");

  uint last_pwr_loss = 0;
  uint last_low_batt = 1;

  time_t time_pwr_loss = 0;
  time_t time_low_batt = 0;

  time_t last_time_pwr_loss = 0;
  time_t last_time_low_batt = 0;

  time_t now = 0;

  while(1) {
    time(&now);

    system_evt_t evt;

    if (xQueueReceive(m_q, &evt, (20 / portTICK_PERIOD_MS)) == pdPASS) {
      ESP_LOGI(TAG, "system task cmd=%d\n", evt.cmd);
    }

    uint pwr_loss = gpio_get_level(GPIO_PIN_N_PWR_LOSS);

    if (pwr_loss != last_pwr_loss) {
      if (pwr_loss == 0) {
        ESP_LOGW(TAG, "power lost!");
        time_pwr_loss = now;
        last_time_pwr_loss = now;
      } else {
        ESP_LOGI(TAG, "power restored!");
      }

      last_pwr_loss = pwr_loss;
    }

    if (pwr_loss == 0) {

        if ((now - last_time_pwr_loss) >= 10) {
          ESP_LOGW(TAG, "power lost for %ld seconds", now - time_pwr_loss);
          last_time_pwr_loss = now;
        }
    }


    uint low_batt = gpio_get_level(GPIO_PIN_LOW_BAT);
    if (low_batt != last_low_batt) {
      if (low_batt == 0) {
        ESP_LOGW(TAG, "low battery detected!");
        time_low_batt = now;
        last_time_low_batt = now;
      } else {
        ESP_LOGI(TAG, "battery voltage OK!");
      }
  }
  if (low_batt == 0) {
    if ((now - last_time_low_batt) >= 10) {
      ESP_LOGE(TAG, "low battery for %ld seconds", now - time_low_batt);
      last_time_low_batt = now;
    }

    if ((now - time_low_batt) >= 60) {
      ESP_LOGW(TAG, "Shutting down in 5 seconds...");
      sdelay(5);
      gpio_set_level(GPIO_PIN_SHUTDOWN, 0);
    }
  }
  last_low_batt = low_batt;
}
}
