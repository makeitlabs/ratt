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
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_system.h"
#include "esp_log.h"

#include "soc/gpio_struct.h"
#include "driver/gpio.h"
#include "system.h"

#include "door_task.h"

static const char *TAG = "door_task";

#define DOOR_QUEUE_DEPTH 8

typedef struct door_evt {
  int unlock;
} door_evt_t;

static QueueHandle_t m_q;

BaseType_t door_unlock(void)
{
    door_evt_t evt;
    evt.unlock = 1;
    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}

BaseType_t door_lock(void)
{
    door_evt_t evt;
    evt.unlock = 0;
    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}


void door_init(void)
{
  m_q = xQueueCreate(DOOR_QUEUE_DEPTH, sizeof(door_evt_t));
  if (m_q == NULL) {
      ESP_LOGE(TAG, "FATAL: Cannot create door queue!");
  }

  gpio_set_direction(GPIO_PIN_MOTOR_O1, GPIO_MODE_OUTPUT);
  gpio_set_direction(GPIO_PIN_MOTOR_O2, GPIO_MODE_OUTPUT);

  gpio_set_level(GPIO_PIN_MOTOR_O1, 1);
  gpio_set_level(GPIO_PIN_MOTOR_O2, 1);
}

void door_delay(int ms)
{
    TickType_t delay = ms / portTICK_PERIOD_MS;
    vTaskDelay(delay);
}

void door_actuate_lock(void)
{
  gpio_set_level(GPIO_PIN_MOTOR_O1, 1);
  gpio_set_level(GPIO_PIN_MOTOR_O2, 0);
  door_delay(500);
  gpio_set_level(GPIO_PIN_MOTOR_O1, 1);
  gpio_set_level(GPIO_PIN_MOTOR_O2, 1);

}

void door_actuate_unlock(void)
{
  gpio_set_level(GPIO_PIN_MOTOR_O1, 0);
  gpio_set_level(GPIO_PIN_MOTOR_O2, 1);
  door_delay(500);
  gpio_set_level(GPIO_PIN_MOTOR_O1, 1);
  gpio_set_level(GPIO_PIN_MOTOR_O2, 1);
}

void door_task(void *pvParameters)
{
    // initially lock after delay
    door_delay(2000);
    door_actuate_lock();

    while(1) {
        door_evt_t evt;

        if (xQueueReceive(m_q, &evt, (20 / portTICK_PERIOD_MS)) == pdPASS) {
          if (evt.unlock) {
            // unlock
            door_actuate_unlock();
          } else {
            // lock
            door_actuate_lock();
          }
        }
    }
}
