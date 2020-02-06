#!/bin/sh

GREEN='\033[1;32m'
CYAN='\033[1;36m'
GRAY='\033[0;37m'

PRODUCTION_DIR=/var/www/authbackend-ng
STAGING_DIR=/var/www/authbackend-ng-staging

cd ssl
echo -e ${GREEN}copying keys and certs to production directory ${PRODUCTION_DIR}...
echo -e ${GRAY}
sudo cp certs/ca.crt ${PRODUCTION_DIR}/ssl
sudo cp certs/client_authbackend.crt ${PRODUCTION_DIR}/ssl
sudo cp private/client_authbackend.key ${PRODUCTION_DIR}/ssl
echo -e ${GREEN}copying keys and certs to staging directory ${STAGING_DIR}...
echo -e ${GRAY}
sudo cp certs/ca.crt ${STAGING_DIR}/ssl
sudo cp certs/client_authbackend.crt ${STAGING_DIR}/ssl
sudo cp private/client_authbackend.key ${STAGING_DIR}/ssl
echo -e ${CYAN}restarting apache...
echo -e ${GRAY}
sudo systemctl restart apache2
