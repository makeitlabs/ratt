#!/bin/sh
CERT_DIR=~/ratt/deployment/certs/mqtt/ssl
mosquitto_pub -h auth --cafile $CERT_DIR/certs/ca.crt --cert $CERT_DIR/certs/client_test.crt --key $CERT_DIR/private/client_test.key -t ratt/control/broadcast/acl/update -n
