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
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"

#include "system.h"

#include "system_task.h"
#include "beep_task.h"
#include "door_task.h"
#include "rfid_task.h"
#include "display_task.h"
#include "net_task.h"
#include "main_task.h"

static const char *TAG = "main_task";

typedef enum {
  STATE_INVALID = 0,
  STATE_INIT,
  STATE_INITIAL_LOCK,
  STATE_START_RFID_READ,
  STATE_WAIT_RFID,
  STATE_RFID_VALID,
  STATE_RFID_INVALID,
  STATE_RFID_INVALID_WAIT,
  STATE_UNLOCKED,
  STATE_LOCK
} main_state_t;

static const char* state_names[] =
  { "STATE_INVALID",
    "STATE_INIT",
    "STATE_INITIAL_LOCK",
    "STATE_START_RFID_READ",
    "STATE_WAIT_RFID",
    "STATE_RFID_VALID",
    "STATE_RFID_INVALID",
    "STATE_RFID_INVALID_WAIT",
    "STATE_UNLOCKED",
    "STATE_LOCK"
  };

typedef struct main_evt {
    main_evt_id_t id;
} main_evt_t;

#define MAIN_QUEUE_DEPTH 8

static QueueHandle_t m_q;

void main_task_init(void)
{
  ESP_LOGI(TAG, "task init");
  m_q = xQueueCreate(MAIN_QUEUE_DEPTH, sizeof(main_evt_t));
  if (m_q == NULL) {
    ESP_LOGE(TAG, "FATAL: Cannot create main task queue!");
  }
}


BaseType_t main_task_event(main_evt_id_t e)
{
    main_evt_t evt;
    evt.id = e;

    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}


void main_task(void *pvParameters)
{
  static member_record_t active_member_record;
  static main_state_t state = STATE_INIT, last_state = STATE_INVALID;
  static TickType_t tick_ms=0, saved_tick_ms=0;

  ESP_LOGI(TAG, "task start, TICK_RATE_HZ=%u", configTICK_RATE_HZ);
  while(1) {
    main_evt_t evt;
    evt.id = MAIN_EVT_NONE;

    tick_ms = xTaskGetTickCount() * (1000 / configTICK_RATE_HZ);

    if (xQueueReceive(m_q, &evt, (20 / portTICK_PERIOD_MS)) == pdPASS) {
      // handle some events immediately, regardless of system state
      switch(evt.id) {
        default:
          break;
      }
    }

    if (state != last_state) {
      ESP_LOGI(TAG, "State change: %s -> %s", state_names[last_state], state_names[state]);
    }
    last_state = state;

    switch(state) {
    case STATE_INIT:
      display_user_msg("Micro-RATT");
      beep_queue(2000, 200, 1, 1);

      state = STATE_INITIAL_LOCK;
      break;

    case STATE_INITIAL_LOCK:
      door_lock();
      state = STATE_START_RFID_READ;
      break;

    case STATE_START_RFID_READ:
      display_clear_msg();
      state = STATE_WAIT_RFID;
      break;

    case STATE_WAIT_RFID:
      switch (evt.id) {
        case MAIN_EVT_VALID_RFID_SCAN:
          state = STATE_RFID_VALID;
          break;
        case MAIN_EVT_INVALID_RFID_SCAN:
          state = STATE_RFID_INVALID;
          break;
        default:
          break;
      }
      break;

    case STATE_RFID_VALID:
      {
        rfid_get_member_record(&active_member_record);

        display_user_msg(active_member_record.name);
        display_allowed_msg("ALLOWED", active_member_record.allowed);

        if (active_member_record.allowed) {
          ESP_LOGI(TAG, "main state member allowed");
          beep_queue(880, 250, 5, 5);
          beep_queue(1174, 250, 5, 5);
          door_unlock();
          saved_tick_ms = tick_ms;
          state = STATE_UNLOCKED;
        } else {
          ESP_LOGI(TAG, "main state member denied");
          beep_queue(220, 250, 5, 5);
          beep_queue(0, 100, 0, 0);
          beep_queue(220, 250, 5, 5);
          saved_tick_ms = tick_ms;
          state = STATE_RFID_INVALID_WAIT;
        }

        net_cmd_queue_access(active_member_record.name, active_member_record.allowed);
      }
      break;

    case STATE_RFID_INVALID:
      {
        rfid_get_member_record(&active_member_record);
        display_user_msg("Unknown Tag");
        display_allowed_msg("DENIED", 0);
        beep_queue(3000, 250, 5, 5);
        beep_queue(0, 100, 0, 0);
        beep_queue(3000, 250, 5, 5);

        char tagstr[12];
        snprintf(tagstr, sizeof(tagstr), "%10.10u", active_member_record.tag);
        net_cmd_queue_access_error("unknown rfid tag", tagstr);
        saved_tick_ms = tick_ms;
        state = STATE_RFID_INVALID_WAIT;
      }
      break;

    case STATE_RFID_INVALID_WAIT:
      if (tick_ms - saved_tick_ms >= 2000)
        state = STATE_START_RFID_READ;
      break;

    case STATE_UNLOCKED:
      if (tick_ms - saved_tick_ms >= 3000)
        state = STATE_LOCK;
      break;

    case STATE_LOCK:
      beep_queue(1174, 250, 5, 5);
      beep_queue(880, 250, 5, 5);
      door_lock();
      state = STATE_START_RFID_READ;
      break;

    default:
      break;
    }

  }
}
