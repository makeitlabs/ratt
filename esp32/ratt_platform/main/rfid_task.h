#ifndef _RFID_TASK_H
#define _RFID_TASK_H

void rfid_init();
void rfid_task(void *pvParameters);


typedef struct user_fields {
    char name[32];
    char last_accessed[32];
    uint8_t allowed;
} user_fields_t;


#endif
