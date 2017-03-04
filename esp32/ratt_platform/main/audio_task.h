#ifndef _AUDIO_TASK_H
#define _AUDIO_TASK_H

void audio_init();
void audio_task(void *pvParameters);


BaseType_t audio_play(char *file);



#endif
