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
#include "system.h"

#include "driver/ledc.h"

static const char *TAG = "beep_task";

#define BEEP_QUEUE_DEPTH 16


#define LEDC_HS_TIMER          LEDC_TIMER_0
#define LEDC_HS_MODE           LEDC_HIGH_SPEED_MODE


ledc_timer_config_t ledc_beep = {
    .duty_resolution = LEDC_TIMER_10_BIT, // resolution of PWM duty
    .freq_hz = 1000,                      // frequency of PWM signal
    .speed_mode = LEDC_HIGH_SPEED_MODE,           // timer mode
    .timer_num = LEDC_HS_TIMER,            // timer index
    .clk_cfg = LEDC_AUTO_CLK,              // Auto select the source clock
};

ledc_channel_config_t ledc_channel = {
    .channel    = LEDC_CHANNEL_0,
    .duty       = 0,
    .gpio_num   = GPIO_PIN_BEEPER,
    .speed_mode = LEDC_HS_MODE,
    .hpoint     = 0,
    .timer_sel  = LEDC_HS_TIMER
};

typedef struct beep_evt {
  int hz;
  int msec;
  int attack;
  int decay;
} beep_evt_t;

static QueueHandle_t m_q;

BaseType_t beep_queue(int hz, int msec, int attack, int decay)
{
    beep_evt_t evt;
    evt.hz = hz;
    evt.msec = msec;
    evt.attack = attack;
    evt.decay = decay;

    return xQueueSendToBack(m_q, &evt, 250 / portTICK_PERIOD_MS);
}

void bdelay(int ms)
{
    TickType_t delay = ms / portTICK_PERIOD_MS;
    vTaskDelay(delay);
}


void beep_init(void)
{
  m_q = xQueueCreate(BEEP_QUEUE_DEPTH, sizeof(beep_evt_t));
  if (m_q == NULL) {
      ESP_LOGE(TAG, "FATAL: Cannot create beeper queue!");
  }

  gpio_config_t beep_gpio_cfg = {
      .pin_bit_mask = GPIO_SEL_BEEPER,
      .mode = GPIO_MODE_OUTPUT,
      .pull_up_en = GPIO_PULLUP_ENABLE,
      .pull_down_en = GPIO_PULLDOWN_DISABLE,
      .intr_type = GPIO_INTR_DISABLE
  };

  ESP_LOGI(TAG, "GPIO configuration...");
  gpio_config(&beep_gpio_cfg);

/*
  for (unsigned int i=0; i<500; i++) {
    gpio_set_level(GPIO_PIN_BEEPER, 1);
    bdelay(10);
    gpio_set_level(GPIO_PIN_BEEPER, 0);
    bdelay(10);
  }
*/

  ESP_LOGI(TAG, "LEDC configuration...");
  ledc_timer_config(&ledc_beep);
  ledc_channel_config(&ledc_channel);

  ledc_fade_func_install(0);
}

void beep_start(int hz, int attack)
{
  ledc_beep.freq_hz = hz;
  ledc_timer_config(&ledc_beep);

  if (hz > 100) {
    ledc_set_fade_with_time(ledc_channel.speed_mode,
            ledc_channel.channel, 900, attack);
    ledc_fade_start(ledc_channel.speed_mode,
            ledc_channel.channel, LEDC_FADE_NO_WAIT);
  }
}

void beep_stop(int decay)
{
  ledc_set_fade_with_time(ledc_channel.speed_mode,
          ledc_channel.channel, 0, decay);
  ledc_fade_start(ledc_channel.speed_mode,
          ledc_channel.channel, LEDC_FADE_NO_WAIT);
}

void beep_delay(int ms)
{
    TickType_t delay = ms / portTICK_PERIOD_MS;
    vTaskDelay(delay);
}

void beep_task(void *pvParameters)
{
    while(1) {
        beep_evt_t evt;

        if (xQueueReceive(m_q, &evt, (20 / portTICK_PERIOD_MS)) == pdPASS) {
            ESP_LOGI(TAG, "beep event hz=%d attack=%d msec=%d decay=%d\n", evt.hz, evt.attack, evt.msec, evt.decay);
            beep_start(evt.hz, evt.attack);
            beep_delay(evt.msec + evt.attack);
            beep_stop(evt.decay);
            beep_delay(evt.decay);
        }
    }
}
