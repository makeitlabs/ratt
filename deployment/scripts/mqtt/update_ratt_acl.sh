#!/bin/sh
CERT_DIR=~/ratt/deployment/certs/mqtt/ssl
BROKER_HOST=$1

if [ -z "$BROKER_HOST" ]; then
    echo "usage: $0 [broker_host]"
    exit 1
fi

mosquitto_pub -h $BROKER_HOST --cafile $CERT_DIR/certs/ca.crt --cert $CERT_DIR/certs/client_test.crt --key $CERT_DIR/private/client_test.key -t ratt/control/broadcast/acl/update -n -d
