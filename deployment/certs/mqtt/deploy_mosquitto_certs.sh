#!/bin/sh

GREEN='\033[1;32m'
CYAN='\033[1;36m'
GRAY='\033[0;37m'

echo -e ${GREEN}copying ssl config...
echo -e ${GRAY}
sudo cp mosquitto_ssl.conf /etc/mosquitto/conf.d
cd ssl
echo -e ${GREEN}copying keys and certs...
echo -e ${GRAY}
sudo cp certs/ca.crt /etc/mosquitto/ca_certificates
sudo cp certs/server.crt /etc/mosquitto/certs
sudo cp private/server.key /etc/mosquitto/certs
echo -e ${CYAN}stopping mosquitto...
echo -e ${GRAY}
sudo service mosquitto stop
echo -e ${CYAN}starting mosquitto...
echo -e ${GRAY}
sudo service mosquitto start
