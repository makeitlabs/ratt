#ifndef _DISPLAY_TASK
#define _DISPLAY_TASK

void display_task(void *pvParameters);
void display_init();

BaseType_t display_wifi_msg(char *msg);
BaseType_t display_wifi_rssi(int16_t rssi);
BaseType_t display_net_msg(char *msg);
BaseType_t display_rfid_msg(char *msg);


#endif
