#ifndef _NET_MQTT
#define _NET_MQTT


int net_mqtt_init(void);
int net_mqtt_start(void);
void net_mqtt_send_wifi_strength(void);
void net_mqtt_send_acl_updated(char* status);
void net_mqtt_send_access(char *member, int allowed);
void net_mqtt_send_access_error(char *err_text, char *err_ext);


#define MQTT_BASE_TOPIC "ratt"
#define MQTT_TOPIC_TYPE_STATUS "status"
#define MQTT_TOPIC_TYPE_CONTROL "control"

#define MQTT_ACL_SUCCESS "downloaded"
#define MQTT_ACL_FAIL "failed"


#endif
