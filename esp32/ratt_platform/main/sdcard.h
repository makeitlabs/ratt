#ifndef _SDCARD_H
#define _SDCARD_H

#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>

void sdcard_init(void);

extern SemaphoreHandle_t g_sdcard_mutex;

#endif
