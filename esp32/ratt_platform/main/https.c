//
// Created by HISONA on 2016. 2. 29..
// see https://github.com/HISONA/https_client for original code base
//
// ported to ESP32 and extended to include client certificates and basic auth support
// by Steve Richardson (steve.richardson@makeitlabs.com) - 2017JAN29
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <signal.h>
#include <sys/socket.h>
#include <unistd.h>
#include <netdb.h>
#include <errno.h>

#include "mbedtls/net.h"
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/error.h"
#include "mbedtls/certs.h"
#include "mbedtls/base64.h"

#include "esp_log.h"

static const char *TAG = "https";

#define CLIENT_PK_PASSPHRASE CONFIG_CLIENT_PK_PASSPHRASE


/*---------------------------------------------------------------------*/
#define H_FIELD_SIZE     512
#define H_PASSPHRASE_SIZE 64
#define H_READ_SIZE     2048
#define CLIENT_MAX         2

typedef struct
{
    int     status;
    char    cookie[H_FIELD_SIZE];
    char    location[H_FIELD_SIZE];
    char    referrer[H_FIELD_SIZE];
    long    content_length;
    int     chunked;
    int     close;

    int     https;
    char    host[256];
    char    port[10];

    long    length;
    char    r_buf[H_READ_SIZE];
    long    r_len;
    int     header_end;

    char    *body;
    long    body_size;
    long    body_len;

    FILE    *fp;
    
    mbedtls_net_context         ssl_fd;
    mbedtls_entropy_context     entropy;
    mbedtls_ctr_drbg_context    ctr_drbg;
    mbedtls_ssl_context         ssl;
    mbedtls_ssl_config          conf;
    mbedtls_x509_crt            cacert;
    mbedtls_x509_crt		client_cert;
    mbedtls_pk_context		client_pk;
    char			client_pk_passphrase[H_PASSPHRASE_SIZE];
    
} HTTP_INFO;

/*---------------------------------------------------------------------*/
static HTTP_INFO http_info[CLIENT_MAX];
static int _error;

/*---------------------------------------------------------------------*/
char *strtoken(char *src, char *dst, int size);

static int parse_url(char *src_url, int *https, char *host, char *port, char *url);
static int http_header(HTTP_INFO *hi, char *param);
static int http_parse(HTTP_INFO *hi);

static int https_init(HTTP_INFO *hi, int https);
static int https_close(HTTP_INFO *hi);
static int https_connect(HTTP_INFO *hi, char *host, char *port);
static int https_write(HTTP_INFO *hi, char *buffer, int len);
static int https_read(HTTP_INFO *hi, char *buffer, int len);

int http_init(int id);
int http_close(int id);

int http_get(int id, char *url, char *auth_user, char *auth_pass, char *response, int size, FILE *fp);
int http_post(int id, char *url, char *data, char *response, int size);

void http_strerror(char *buf, int len);
int http_open_chunked(int id, char *url, char *auth_user, char *auth_pass);
int http_write_chunked(int id, char *data, int len);
int http_read_chunked(int id, char *response, int size);


/*---------------------------------------------------------------------------*/
char *strtoken(char *src, char *dst, int size)
{
    char *p, *st, *ed;
    int  len = 0;

    // l-trim
    p = src;

    while(1)
    {
        if((*p == '\n') || (*p == 0)) return NULL; /* value is not exists */
        if((*p != ' ') && (*p != '\t')) break;
        p++;
    }

    st = p;
    while(1)
    {
        ed = p;
        if(*p == ' ') {
            p++;
            break;
        }
        if((*p == '\n') || (*p == 0)) break;
        p++;
    }

    // r-trim
    while(1)
    {
        ed--;
        if(st == ed) break;
        if((*ed != ' ') && (*ed != '\t')) break;
    }

    len = (int)(ed - st + 1);
    if((size > 0) && (len >= size)) len = size - 1;

    strncpy(dst, st, len);
    dst[len]=0;

    return p;
}

/*---------------------------------------------------------------------*/
static int parse_url(char *src_url, int *https, char *host, char *port, char *url)
{
    char *p1, *p2;
    char str[1024];

    memset(str, 0, 1024);

    if(strncmp(src_url, "http://", 7)==0) {
        p1=&src_url[7];
        *https = 0;
    } else if(strncmp(src_url, "https://", 8)==0) {
        p1=&src_url[8];
        *https = 1;
    } else {
        p1 = &src_url[0];
        *https = 0;
    }

    if((p2=strstr(p1, "/")) == NULL)
    {
        sprintf(str, "%s", p1);
        sprintf(url, "/");
    }
    else
    {
        strncpy(str, p1, p2-p1);
        snprintf(url, 256, "%s", p2);
    }

    if((p1=strstr(str, ":")) != NULL)
    {
        *p1=0;
        snprintf(host, 256, "%s", str);
        snprintf(port, 5, "%s", p1+1);
    }
    else
    {
        snprintf(host, 256, "%s", str);

        if(*https == 0)
            snprintf(port, 5, "80");
        else
            snprintf(port, 5, "443");
    }

    return 0;

}

/*---------------------------------------------------------------------*/
static int http_header(HTTP_INFO *hi, char *param)
{
    char *token;
    char t1[256], t2[256];
    int  len;

    token = param;

    if((token=strtoken(token, t1, 256)) == 0) return -1;
    if((token=strtoken(token, t2, 256)) == 0) return -1;

    if(strncasecmp(t1, "HTTP", 4) == 0)
    {
        hi->status = atoi(t2);
    }
    else if(strncasecmp(t1, "set-cookie:", 11) == 0)
    {
        snprintf(hi->cookie, 512, "Cookie: %s\r\n", t2);
    }
    else if(strncasecmp(t1, "location:", 9) == 0)
    {
        len = (int)strlen(t2);
        strncpy(hi->location, t2, len);
        hi->location[len] = 0;
    }
    else if(strncasecmp(t1, "content-length:", 15) == 0)
    {
        hi->content_length = atoi(t2);
    }
    else if(strncasecmp(t1, "transfer-encoding:", 18) == 0)
    {
        if(strncasecmp(t2, "chunked", 7) == 0)
        {
            hi->chunked = 1;
        }
    }
    else if(strncasecmp(t1, "connection:", 11) == 0)
    {
        if(strncasecmp(t2, "close", 5) == 0)
        {
            hi->close = 1;
        }
    }

    return 1;
}

/*---------------------------------------------------------------------*/
static int http_parse(HTTP_INFO *hi)
{
    char    *p1, *p2;
    long    len;

    if(hi->r_len <= 0) return -1;

    p1 = hi->r_buf;

    while(1) {
        if(hi->header_end == 0) {
            // header parser            
            if((p2 = strstr(p1, "\r\n")) != NULL) {
                len = (long)(p2 - p1);
                *p2 = 0;
                
                if(len > 0) {
                    // printf("header: %s(%ld)\n", p1, len);

                    http_header(hi, p1);
                    p1 = p2 + 2;    // skip CR+LF
                } else {
                    hi->header_end = 1; // reach the header-end.

                    // printf("header_end .... \n");

                    p1 = p2 + 2;    // skip CR+LF

                    if(hi->chunked == 1) {
                        len = hi->r_len - (p1 - hi->r_buf);
                        if(len > 0) {
                            if((p2 = strstr(p1, "\r\n")) != NULL) {
                                *p2 = 0;

                                if((hi->length = strtol(p1, NULL, 16)) == 0) {
                                    hi->chunked = 0;
                                } else {
                                    hi->content_length += hi->length;
                                }
                                p1 = p2 + 2;    // skip CR+LF
                            } else {
                                // copy the data as chunked size ...
                                strncpy(hi->r_buf, p1, len);
                                hi->r_buf[len] = 0;
                                hi->r_len = len;
                                hi->length = -1;
                                break;
                            }
                        } else {
                            hi->r_len = 0;
                            hi->length = -1;
                            break;
                        }
                    } else {
                        hi->length = hi->content_length;
                    }
                }
            } else {
                len = hi->r_len - (p1 - hi->r_buf);
                if(len  > 0) {
                    // keep the partial header data ...
                    strncpy(hi->r_buf, p1, len);
                    hi->r_buf[len] = 0;
                    hi->r_len = len;
                } else {
                    hi->r_len = 0;
                }
                break;
            }
        } else {
            // body parser ...
            if(hi->chunked == 1 && hi->length == -1) {
                len = hi->r_len - (p1 - hi->r_buf);
                if(len > 0) {
                    if ((p2 = strstr(p1, "\r\n")) != NULL) {
                        *p2 = 0;

                        if((hi->length = strtol(p1, NULL, 16)) == 0) {
                            hi->chunked = 0;
                        } else {
                            hi->content_length += hi->length;
                        }
                        p1 = p2 + 2;    // skip CR+LF
                    } else {
                        // copy the remain data as chunked size ...
                        strncpy(hi->r_buf, p1, len);
                        hi->r_buf[len] = 0;
                        hi->r_len = len;
                        hi->length = -1;
                        break;
                    }
                } else {
                    hi->r_len = 0;
                    break;
                }
            } else {
                if(hi->length > 0) {
                    len = hi->r_len - (p1 - hi->r_buf);

                    if(len > hi->length) {
                        // copy the data for response ..

                        if (hi->fp) {
                            size_t ret = fwrite(p1, 1, hi->length, hi->fp);
                            if (ret != hi->length) {
                                ESP_LOGE(TAG, "error writing to file ret=%d, err=%d", ret, ferror(hi->fp));
                                return -1;
                            }
                        } else {
                            if(hi->body_len < hi->body_size-1) {
                                // if there is still room in the body buffer...
                                
                                if (hi->body_size > (hi->body_len + hi->length)) {
                                    // if there is room for the whole rcv buf to be copied into body buf...
                                    // copy all bytes from rcv buf
                                    
                                    strncpy(&(hi->body[hi->body_len]), p1, hi->length);
                                    hi->body_len += hi->length;
                                    hi->body[hi->body_len] = 0;
                                } else {
                                    // there are more bytes in the rcv buf than will fit in the body buffer...
                                    // only copy as many as will fit
                                    
                                    strncpy(&(hi->body[hi->body_len]), p1, hi->body_size - hi->body_len - 1);
                                    hi->body_len = hi->body_size - 1;
                                    hi->body[hi->body_len] = 0;
                                }
                            }
                        }

                        p1 += hi->length;
                        len -= hi->length;

                        if(hi->chunked == 1 && len >= 2) {
                            p1 += 2;    // skip CR+LF
                            hi->length = -1;
                        } else {
                            return -1;
                        }
                    } else {
                        // copy the data for response ..

                        if (hi->fp) {
                            size_t ret = fwrite(p1, 1, len, hi->fp);
                            if (ret != len) {
                                ESP_LOGE(TAG, "error writing to file ret=%d, err=%d", ret, ferror(hi->fp));
                                return -1;
                            }
                        } else {
                            if(hi->body_len < hi->body_size-1) {
                                // if there is still room in the body buffer...
                                
                                if (hi->body_size > (hi->body_len + len)) {
                                    // if there is room for 'len' bytes to be copied into body buf...
                                    // copy 'len' bytes from rcv buf
                                    
                                    strncpy(&(hi->body[hi->body_len]), p1, len);
                                    hi->body_len += len;
                                    hi->body[hi->body_len] = 0;
                                } else {
                                    // 'len' is more bytes than will fit in the body buffer...
                                    // only copy as many as will fit 
                                    
                                    strncpy(&(hi->body[hi->body_len]), p1, hi->body_size - hi->body_len - 1);
                                    hi->body_len = hi->body_size - 1;
                                    hi->body[hi->body_len] = 0;
                                }
                            }
                        }

                        hi->length -= len;
                        hi->r_len = 0;

                        if(hi->chunked == 0 && hi->length <= 0) return 1;

                        break;
                    }
                } else {
                    if(hi->chunked == 0) return 1;

                    // chunked size check ..
                    if((hi->r_len > 2) && (memcmp(p1, "\r\n", 2) == 0)) {
                        p1 += 2;
                        hi->length = -1;
                    } else {
                        hi->length = -1;
                        hi->r_len = 0;
                    }
                }
            }
        }
    }
    
    return 0;
}

/*---------------------------------------------------------------------*/
static int https_init(HTTP_INFO *hi, int https)
{
    memset(hi, 0, sizeof(HTTP_INFO));

    ESP_LOGI(TAG, "https_init() https=%d", https);
    
    if(https == 1)
    {
        mbedtls_ssl_init(&hi->ssl);
        mbedtls_ssl_config_init(&hi->conf);
        mbedtls_x509_crt_init(&hi->cacert);
        mbedtls_x509_crt_init(&hi->client_cert);
        mbedtls_pk_init(&hi->client_pk);

        mbedtls_ctr_drbg_init(&hi->ctr_drbg);
    }

    mbedtls_net_init(&hi->ssl_fd);

    hi->https = https;
    
    return 0;
}

/*---------------------------------------------------------------------*/
static int https_close(HTTP_INFO *hi)
{
    if(hi->https == 1)
    {
        mbedtls_ssl_close_notify(&hi->ssl);
    }

    mbedtls_net_free( &hi->ssl_fd );

    if(hi->https == 1)
    {
        mbedtls_x509_crt_free(&hi->cacert);
        mbedtls_x509_crt_free(&hi->client_cert);
        mbedtls_pk_free(&hi->client_pk);
        mbedtls_ssl_free(&hi->ssl);
        mbedtls_ssl_config_free(&hi->conf);
        mbedtls_ctr_drbg_free(&hi->ctr_drbg);
        mbedtls_entropy_free(&hi->entropy);
    }

    ESP_LOGI(TAG, "https_close()");

    return 0;
}

/*
 * Initiate a TCP connection with host:port and the given protocol
 * waiting for timeout (ms)
 */
static int mbedtls_net_connect_timeout( mbedtls_net_context *ctx, const char *host, const char *port,
                                        int proto, uint32_t timeout )
{
    int ret;
    struct addrinfo hints, *addr_list, *cur;


    /* Do name resolution with both IPv6 and IPv4 */
    memset( &hints, 0, sizeof( hints ) );
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = proto == MBEDTLS_NET_PROTO_UDP ? SOCK_DGRAM : SOCK_STREAM;
    hints.ai_protocol = proto == MBEDTLS_NET_PROTO_UDP ? IPPROTO_UDP : IPPROTO_TCP;

    if( getaddrinfo( host, port, &hints, &addr_list ) != 0 )
        return( MBEDTLS_ERR_NET_UNKNOWN_HOST );

    /* Try the sockaddrs until a connection succeeds */
    ret = MBEDTLS_ERR_NET_UNKNOWN_HOST;
    for( cur = addr_list; cur != NULL; cur = cur->ai_next )
    {
        ctx->fd = (int) socket( cur->ai_family, cur->ai_socktype,
                                cur->ai_protocol );
        if( ctx->fd < 0 )
        {
            ret = MBEDTLS_ERR_NET_SOCKET_FAILED;
            continue;
        }

        if( mbedtls_net_set_nonblock( ctx ) < 0 )
        {
            close( ctx->fd );
            ctx->fd = -1;
            ret = MBEDTLS_ERR_NET_CONNECT_FAILED;
            break;
        }

        if( connect( ctx->fd, cur->ai_addr, cur->ai_addrlen ) == 0 )
        {
            ret = 0;
            break;
        }
        else if( errno == EINPROGRESS )
        {
            int            fd = (int)ctx->fd;
            int            opt;
            socklen_t      slen;
            struct timeval tv;
            fd_set         fds;

            while(1)
            {
                FD_ZERO( &fds );
                FD_SET( fd, &fds );

                tv.tv_sec  = timeout / 1000;
                tv.tv_usec = ( timeout % 1000 ) * 1000;

                ret = select( fd+1, NULL, &fds, NULL, timeout == 0 ? NULL : &tv );
                if( ret == -1 )
                {
                    if(errno == EINTR) continue;
                }
                else if( ret == 0 )
                {
                    close( fd );
                    ctx->fd = -1;
                    ret = MBEDTLS_ERR_NET_CONNECT_FAILED;
                }
                else
                {
                    ret = 0;

                    slen = sizeof(int);
                    if( (getsockopt(fd, SOL_SOCKET, SO_ERROR, (void *)&opt, &slen) == 0) && (opt > 0) )
                    {
                        close( fd );
                        ctx->fd = -1;
                        ret = MBEDTLS_ERR_NET_CONNECT_FAILED;
                    }
                }

                break;
            }

            break;
        }

        close( ctx->fd );
        ctx->fd = -1;
        ret = MBEDTLS_ERR_NET_CONNECT_FAILED;
    }

    freeaddrinfo( addr_list );

    if( (ret == 0) && (mbedtls_net_set_block( ctx ) < 0) )
    {
        close( ctx->fd );
        ctx->fd = -1;
        ret = MBEDTLS_ERR_NET_CONNECT_FAILED;
    }

    return( ret );
}

/*---------------------------------------------------------------------*/
static int https_connect(HTTP_INFO *hi, char *host, char *port)
{
    int ret, https;

    extern const uint8_t ca_cert_pem_start[] asm("_binary_cacert_pem_start");
    extern const uint8_t ca_cert_pem_end[]   asm("_binary_cacert_pem_end");
    
    extern const uint8_t client_cert_pem_start[] asm("_binary_client_cert_pem_start");
    extern const uint8_t client_cert_pem_end[]   asm("_binary_client_cert_pem_end");
    
    extern const uint8_t client_key_pem_start[] asm("_binary_client_key_pem_start");
    extern const uint8_t client_key_pem_end[]   asm("_binary_client_key_pem_end");

    https = hi->https;

    if(https == 1)
    {
        mbedtls_entropy_init( &hi->entropy );

        ESP_LOGI(TAG, "Seeding random number generator...");
        ret = mbedtls_ctr_drbg_seed( &hi->ctr_drbg, mbedtls_entropy_func, &hi->entropy, NULL, 0);
        if( ret != 0 )
        {
            return ret;
        }

        ESP_LOGI(TAG, "Loading CA root certificate...");
        ret = mbedtls_x509_crt_parse( &hi->cacert, ca_cert_pem_start,
                                      ca_cert_pem_end - ca_cert_pem_start );
        if( ret < 0 )
        {
            ESP_LOGE(TAG, "mbedtls_x509_crt_parse returned -0x%x\n\n", -ret);
            return ret;
        }

        ESP_LOGI(TAG, "Loading client certificate...");
        ret = mbedtls_x509_crt_parse( &hi->client_cert, client_cert_pem_start,
                                      client_cert_pem_end - client_cert_pem_start );
        if( ret < 0 )
        {
            ESP_LOGE(TAG, "mbedtls_x509_crt_parse returned -0x%x\n\n", -ret);
            return ret;
        }

        ESP_LOGI(TAG, "Loading client key...");
        snprintf(hi->client_pk_passphrase, sizeof(hi->client_pk_passphrase) - 1, CLIENT_PK_PASSPHRASE);
        ret = mbedtls_pk_parse_key(&hi->client_pk, client_key_pem_start,
                                   client_key_pem_end - client_key_pem_start,
                                   (const unsigned char*) hi->client_pk_passphrase,
                                   strlen(hi->client_pk_passphrase));
        if(ret < 0)
        {
            ESP_LOGE(TAG, "mbedtls_pk_parse_key returned -0x%x\n\n", -ret);
            return ret;
        }        
        
        ret = mbedtls_ssl_config_defaults( &hi->conf,
                                           MBEDTLS_SSL_IS_CLIENT,
                                           MBEDTLS_SSL_TRANSPORT_STREAM,
                                           MBEDTLS_SSL_PRESET_DEFAULT );
        if( ret != 0 )
        {
            return ret;
        }

        // MBEDTLS_SSL_VERIFY_REQUIRED means the CA verification must succeed to connect        
        mbedtls_ssl_conf_authmode(&hi->conf, MBEDTLS_SSL_VERIFY_REQUIRED);

        // set up our own client certificate
        mbedtls_ssl_conf_own_cert(&hi->conf, &hi->client_cert, &hi->client_pk);

        // set up CA certificate
        mbedtls_ssl_conf_ca_chain( &hi->conf, &hi->cacert, NULL );

        mbedtls_ssl_conf_rng( &hi->conf, mbedtls_ctr_drbg_random, &hi->ctr_drbg );
        mbedtls_ssl_conf_read_timeout( &hi->conf, 5000 );

        ret = mbedtls_ssl_setup( &hi->ssl, &hi->conf );
        if( ret != 0 )
        {
            return ret;
        }

        ret = mbedtls_ssl_set_hostname( &hi->ssl, host );
        if( ret != 0 )
        {
            return ret;
        }
    }

    ret = mbedtls_net_connect_timeout(&hi->ssl_fd, host, port, MBEDTLS_NET_PROTO_TCP, 5000);
    if( ret != 0 )
    {
        return ret;
    }

    if(https == 1)
    {
        mbedtls_ssl_set_bio(&hi->ssl, &hi->ssl_fd, mbedtls_net_send, mbedtls_net_recv, mbedtls_net_recv_timeout);

        while ((ret = mbedtls_ssl_handshake(&hi->ssl)) != 0)
        {
            if (ret != MBEDTLS_ERR_SSL_WANT_READ && ret != MBEDTLS_ERR_SSL_WANT_WRITE)
            {
                return ret;
            }
        }
    }

    return 0;
}

/*---------------------------------------------------------------------*/
static int https_write(HTTP_INFO *hi, char *buffer, int len)
{
    int ret, slen = 0;

    while(1)
    {
        if(hi->https == 1)
            ret = mbedtls_ssl_write(&hi->ssl, (u_char *)&buffer[slen], (size_t)(len-slen));
        else
            ret = mbedtls_net_send(&hi->ssl_fd, (u_char *)&buffer[slen], (size_t)(len-slen));

        if(ret == MBEDTLS_ERR_SSL_WANT_WRITE) continue;
        else if(ret <= 0) return ret;

        slen += ret;

        if(slen >= len) break;
    }

    return slen;
}

/*---------------------------------------------------------------------*/
static int https_read(HTTP_INFO *hi, char *buffer, int len)
{
    if(hi->https == 1)
    {
        return mbedtls_ssl_read(&hi->ssl, (u_char *)buffer, (size_t)len);
    }
    else
    {
        return mbedtls_net_recv_timeout(&hi->ssl_fd, (u_char *)buffer, (size_t)len, 5000);
    }
}

/*---------------------------------------------------------------------*/
int http_init(int id)
{
    HTTP_INFO *hi;

    if(id >= CLIENT_MAX) return -1;
    hi = &http_info[id];

    return https_init(hi, 0);
}

/*---------------------------------------------------------------------*/
int http_close(int id)
{
    HTTP_INFO *hi;

    if(id >= CLIENT_MAX) return -1;
    hi = &http_info[id];

    return https_close(hi);
}

/*---------------------------------------------------------------------*/
int http_get(int id, char *url, char *auth_user, char *auth_pass, char *response, int size, FILE* fp)
{
    HTTP_INFO   *hi;
    char        request[1024], err[100];
    char        host[256], port[10], dir[1024];
    int         sock_fd, https, ret, opt, len;
    socklen_t   slen;


    if(id > 1) return -1;
    hi = &http_info[id];

    parse_url(url, &https, host, port, dir);

    if( (hi->ssl_fd.fd == -1) || (hi->https != https) ||
        (strcmp(hi->host, host) != 0) || (strcmp(hi->port, port) != 0) )
    {
        https_close(hi);

        https_init(hi, https);

        if((ret=https_connect(hi, host, port)) < 0)
        {
            https_close(hi);

            mbedtls_strerror(ret, err, 100);
            snprintf(response, 256, "socket error: %s(%d)", err, ret);
            return -1;
        }
    }
    else
    {
        sock_fd = hi->ssl_fd.fd;

        slen = sizeof(int);

        if((getsockopt(sock_fd, SOL_SOCKET, SO_ERROR, (void *)&opt, &slen) < 0) || (opt > 0))
        {
            https_close(hi);

            https_init(hi, https);

            if((ret=https_connect(hi, host, port)) < 0)
            {
                https_close(hi);

                mbedtls_strerror(ret, err, 100);
                snprintf(response, 256, "socket error: %s(%d)", err, ret);
                return -1;
            }
        }
    }

    /* Send HTTP request. */
    
    // build the http request, including an auth header if requested
    if (strcmp(auth_user, "") != 0) {
        size_t olen;
        unsigned char base64[32];
        char auth[64];
        
        snprintf(auth, sizeof(auth), "%s:%s", auth_user, auth_pass);
        if ((ret = mbedtls_base64_encode(base64, 32, &olen, (const unsigned char*)auth, strlen(auth))) != 0) {
            ESP_LOGE(TAG, "mbedtls_base64_encode returned -0x%x\n\n", -ret);
            abort();
        }
        
        snprintf(auth, sizeof(auth), "Authorization: Basic %s", base64);
        
        // basic auth required
        len = snprintf(request, sizeof(request),
                 "GET %s HTTP/1.1\n"
                 "Host: %s:%s\n"
                 "%s\n"
                 "User-Agent: esp-idf/1.0 esp32\n"
                 "Connection: close\n"
                 "\n", dir, host, port, auth);
    } else {
        // no basic auth required
        len = snprintf(request, sizeof(request),
                 "GET %s HTTP/1.1\n"
                 "Host: %s:%s\n"
                 "User-Agent: esp-idf/1.0 esp32\n"
                 "Connection: close\n"
                 "\n", dir, host, port);
        
    }
    
    ESP_LOGI(TAG, "request header:\n%s", request);
    
    if((ret = https_write(hi, request, len)) != len)
    {
        https_close(hi);

        mbedtls_strerror(ret, err, 100);

        snprintf(response, 256, "socket error: %s(%d)", err, ret);

        return -1;
    }

    hi->status = 0;
    hi->r_len = 0;
    hi->header_end = 0;
    hi->content_length = 0;
    hi->close = 0;

    if (fp) {
        hi->body = 0;
        hi->body_size = 0;
        hi->body_len = 0;
    } else {
        hi->body = response;
        hi->body_size = size;
        hi->body_len = 0;
    }
    hi->fp = fp;
    
    while(1)
    {
        ret = https_read(hi, &hi->r_buf[hi->r_len], (int)(H_READ_SIZE - hi->r_len));
        if(ret == MBEDTLS_ERR_SSL_WANT_READ) continue;
        else if(ret < 0)
        {
            https_close(hi);

            mbedtls_strerror(ret, err, 100);

            snprintf(response, 256, "socket error: %s(%d)", err, ret);

            return -1;
        }
        else if(ret == 0)
        {
            https_close(hi);
            break;
        }

        hi->r_len += ret;
        hi->r_buf[hi->r_len] = 0;

        // printf("read(%ld): |%s| \n", hi->r_len, hi->r_buf);
        // printf("read(%ld) ... \n", hi->r_len);

        if(http_parse(hi) != 0) break;
    }

    if(hi->close == 1)
    {
        https_close(hi);
    }
    else
    {
        strncpy(hi->host, host, strlen(host));
        strncpy(hi->port, port, strlen(port));
    }

    /*
    printf("status: %d \n", hi->status);
    printf("cookie: %s \n", hi->cookie);
    printf("location: %s \n", hi->location);
    printf("referrer: %s \n", hi->referrer);
    printf("length: %ld \n", hi->content_length);
    printf("body: %ld \n", hi->body_len);
    */

    return hi->status;
}

/*---------------------------------------------------------------------*/
int http_post(int id, char *url, char *data, char *response, int size)
{
    HTTP_INFO   *hi;
    char        request[1024], err[100];
    char        host[256], port[10], dir[1024];
    int         sock_fd, https, ret, opt, len;
    socklen_t   slen;


    if(id > 1) return -1;
    hi = &http_info[id];

    parse_url(url, &https, host, port, dir);

    if( (hi->ssl_fd.fd == -1) || (hi->https != https) ||
        (strcmp(hi->host, host) != 0) || (strcmp(hi->port, port) != 0) )
    {
        if(hi->ssl_fd.fd != -1)
            https_close(hi);

        https_init(hi, https);

        if((ret=https_connect(hi, host, port)) < 0)
        {
            https_close(hi);

            mbedtls_strerror(ret, err, 100);
            snprintf(response, 256, "socket error: %s(%d)", err, ret);

            return -1;
        }
    }
    else
    {
        sock_fd = hi->ssl_fd.fd;

        slen = sizeof(int);

        if((getsockopt(sock_fd, SOL_SOCKET, SO_ERROR, (void *)&opt, &slen) < 0) || (opt > 0))
        {
            https_close(hi);

            https_init(hi, https);

            if((ret=https_connect(hi, host, port)) < 0)
            {
                https_close(hi);

                mbedtls_strerror(ret, err, 100);
                snprintf(response, 256, "socket error: %s(%d)", err, ret);

                return -1;
            }
        }
//      else
//          printf("socket reuse: %d \n", sock_fd);
    }

    /* Send HTTP request. */
    len = snprintf(request, 1024,
            "POST %s HTTP/1.1\r\n"
            "User-Agent: Mozilla/4.0\r\n"
            "Host: %s:%s\r\n"
            "Content-Type: application/json; charset=utf-8\r\n"
            "Content-Length: %d\r\n"
            "Connection: Keep-Alive\r\n"
            "%s\r\n"
            "%s",
            dir, host, port, (int)strlen(data), hi->cookie, data);

    if((ret = https_write(hi, request, len)) != len)
    {
        https_close(hi);

        mbedtls_strerror(ret, err, 100);

        snprintf(response, 256, "socket error: %s(%d)", err, ret);

        return -1;
    }

//  printf("request: %s \r\n\r\n", request);

    hi->status = 0;
    hi->r_len = 0;
    hi->header_end = 0;
    hi->content_length = 0;
    hi->close = 0;

    hi->body = response;
    hi->body_size = size;
    hi->body_len = 0;

    hi->body[0] = 0;

    while(1)
    {
        ret = https_read(hi, &hi->r_buf[hi->r_len], (int)(H_READ_SIZE - hi->r_len));
        if(ret == MBEDTLS_ERR_SSL_WANT_READ) continue;
        else if(ret < 0)
        {
            https_close(hi);

            mbedtls_strerror(ret, err, 100);

            snprintf(response, 256, "socket error: %s(%d)", err, ret);

            return -1;
        }
        else if(ret == 0)
        {
            https_close(hi);
            break;
        }

        hi->r_len += ret;
        hi->r_buf[hi->r_len] = 0;

//        printf("read(%ld): %s \n", hi->r_len, hi->r_buf);
//        printf("read(%ld) \n", hi->r_len);

        if(http_parse(hi) != 0) break;
    }

    if(hi->close == 1)
    {
        https_close(hi);
    }
    else
    {
        strncpy(hi->host, host, strlen(host));
        strncpy(hi->port, port, strlen(port));
    }

/*
    printf("status: %d \n", hi->status);
    printf("cookie: %s \n", hi->cookie);
    printf("location: %s \n", hi->location);
    printf("referrer: %s \n", hi->referrer);
    printf("length: %d \n", hi->content_length);
    printf("body: %d \n", hi->body_len);
*/

    return hi->status;

}

/*---------------------------------------------------------------------*/
void http_strerror(char *buf, int len)
{
    mbedtls_strerror(_error, buf, len);
}

/*---------------------------------------------------------------------*/


int http_open_chunked(int id, char *url, char *auth_user, char *auth_pass)
{
    HTTP_INFO *hi;
    char request[1024];
    char host[256], port[10], dir[1024];
    int sock_fd, https, ret, opt, len;
    socklen_t slen;


    if (id > 1) return -1;
    hi = &http_info[id];

    parse_url(url, &https, host, port, dir);

    if ((hi->ssl_fd.fd == -1) || (hi->https != https) ||
        (strcmp(hi->host, host) != 0) || (strcmp(hi->port, port) != 0))
    {
        if (hi->ssl_fd.fd != -1)
            https_close(hi);

        https_init(hi, https);

        if ((ret = https_connect(hi, host, port)) < 0)
        {
            https_close(hi);

            _error = ret;

            return -1;
        }
    }
    else
    {
        sock_fd = hi->ssl_fd.fd;

        slen = sizeof(int);

        if ((getsockopt(sock_fd, SOL_SOCKET, SO_ERROR, (void *) &opt, &slen) < 0) || (opt > 0))
        {
            https_close(hi);

            https_init(hi, https);

            if ((ret = https_connect(hi, host, port)) < 0)
            {
                https_close(hi);

                _error = ret;

                return -1;
            }
        }
//      else
//          printf("socket reuse: %d \n", sock_fd);
    }


//
    
    // build the http request, including an auth header if requested
    if (strcmp(auth_user, "") != 0) {
        size_t olen;
        unsigned char base64[32];
        char auth[64];
        
        snprintf(auth, sizeof(auth), "%s:%s", auth_user, auth_pass);
        if ((ret = mbedtls_base64_encode(base64, 32, &olen, (const unsigned char*)auth, strlen(auth))) != 0) {
            ESP_LOGE(TAG, "mbedtls_base64_encode returned -0x%x\n\n", -ret);
            abort();
        }
        
        snprintf(auth, sizeof(auth), "Authorization: Basic %s", base64);
        
        // basic auth required
        len = snprintf(request, sizeof(request),
                       "GET %s HTTP/1.1\r\n"
                       "Host: %s:%s\r\n"
                       "%s\r\n"
                       "User-Agent: esp-idf/1.0 esp32\r\n"
                       "Transfer-Encoding: chunked\r\n"
                       "Connection: Keep-Alive\r\n"
                       "%s\r\n", dir, host, port, auth, hi->cookie);
    } else {
        // no basic auth required
        len = snprintf(request, sizeof(request),
                       "GET %s HTTP/1.1\r\n"
                       "Host: %s:%s\r\n"
                       "User-Agent: esp-idf/1.0 esp32\r\n"
                       "Transfer-Encoding: chunked\r\n"
                       "Connection: Keep-Alive\r\n"
                       "%s\r\n", dir, host, port, hi->cookie);
        
    }

    ESP_LOGI(TAG, "request:\n\r %s", request);


    /* Send HTTP request. */
    /*
    len = snprintf(request, 1024,
                   "POST %s HTTP/1.1\r\n"
                           "User-Agent: Mozilla/4.0\r\n"
                           "Host: %s:%s\r\n"
                           "Content-Type: application/json; charset=utf-8\r\n"
                           "Transfer-Encoding: chunked\n"
                           "Connection: Keep-Alive\n"
                           "%s\r\n",
                   dir, host, port, hi->cookie);
    */
    
    if ((ret = https_write(hi, request, len)) != len)
    {
        https_close(hi);

        _error = ret;

        return -1;
    }

    strncpy(hi->host, host, strlen(host));
    strncpy(hi->port, port, strlen(port));

    return 0;
}

/*---------------------------------------------------------------------*/
int http_write_chunked(int id, char *data, int len)
{
    HTTP_INFO *hi;
    char str[10];
    int ret, l;


    if (id > 1) return -1;
    hi = &http_info[id];

    l = snprintf(str, 10, "%x\r\n", len);

    if ((ret = https_write(hi, str, l)) != l)
    {
        https_close(hi);
        _error = ret;

        return -1;
    }

    if ((ret = https_write(hi, data, len)) != len)
    {
        https_close(hi);
        _error = ret;

        return -1;
    }

    if ((ret = https_write(hi, "\r\n", 2)) != 2)
    {
        https_close(hi);
        _error = ret;

        return -1;
    }

    return len;
}

/*---------------------------------------------------------------------*/
int http_read_chunked(int id, char *response, int size)
{
    HTTP_INFO *hi;
    int ret;


    if (id > 1) return -1;
    hi = &http_info[id];

    if ((ret = https_write(hi, "0\r\n\r\n", 5)) != 5)
    {
        https_close(hi);
        _error = ret;

        return -1;
    }

    hi->status = 0;
    hi->r_len = 0;
    hi->header_end = 0;
    hi->content_length = 0;
    hi->close = 0;

    hi->body = response;
    hi->body_size = size;
    hi->body_len = 0;

    hi->body[0] = 0;

    while(1)
    {
        ret = https_read(hi, &hi->r_buf[hi->r_len], (int)(H_READ_SIZE - hi->r_len));
        if(ret == MBEDTLS_ERR_SSL_WANT_READ) continue;
        else if(ret < 0)
        {
            https_close(hi);
            _error = ret;

            return -1;
        }
        else if(ret == 0)
        {
            https_close(hi);
            break;
        }

        hi->r_len += ret;
        hi->r_buf[hi->r_len] = 0;

        //printf("read(%ld): %s \n", hi->r_len, hi->r_buf);
        //printf("read(%ld) \n", hi->r_len);

        if(http_parse(hi) != 0) break;
    }

    if(hi->close == 1)
    {
        https_close(hi);
    }

/*
    printf("status: %d \n", hi->status);
    printf("cookie: %s \n", hi->cookie);
    printf("location: %s \n", hi->location);
    printf("referrer: %s \n", hi->referrer);
    printf("length: %d \n", hi->content_length);
    printf("body: %d \n", hi->body_len);
*/

    return hi->status;
}

