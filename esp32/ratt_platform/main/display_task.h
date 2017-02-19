#ifndef _DISPLAY_TASK
#define _DISPLAY_TASK

void display_task(void *pvParameters);
void display_init();

BaseType_t display_wifi_msg(char *msg);
BaseType_t display_wifi_rssi(int16_t rssi);
BaseType_t display_net_msg(char *msg);
BaseType_t display_user_msg(char *msg);
BaseType_t display_allowed_msg(char *msg, uint8_t allowed);


#endif
