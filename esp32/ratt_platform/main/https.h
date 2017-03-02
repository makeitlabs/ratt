//
// Created by HISONA on 2016. 2. 29..
//

#ifndef HTTPS_CLIENT_HTTPS_H
#define HTTPS_CLIENT_HTTPS_H

/*---------------------------------------------------------------------*/

char *strtoken(char *src, char *dst, int size);

int  http_init(int id);
int  http_close(int id);
int  http_get(int id, char *url, char *auth_user, char *auth_pass, char *response, int size, FILE* fp);
int  http_post(int id, char *url, char *data, char *response, int size);

void http_strerror(char *buf, int len);
int  http_open_chunked(int id, char *url, char *auth_user, char *auth_pass);
int  http_write_chunked(int id, char *data, int len);
int  http_read_chunked(int id, char *response, int size);

#endif //HTTPS_CLIENT_HTTPS_H

