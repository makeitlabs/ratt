#!/bin/sh

RED='\033[1;31m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
GRAY='\033[0;37m'
WHITE='\033[1;37m'

CN=$1

if [ -z $CN ]; then
    echo -e ${RED}Must pass CN for client on command line
    echo -e ${GRAY}
    exit 1
else
    clear
    echo -e ${WHITE}CN is ${CYAN}${CN}
    echo -e ${GRAY}
fi

cd ssl

echo -e ${GREEN}generate client key without encryption
echo -e ${GRAY}
openssl genrsa -out private/client_${CN}.key 2048 -config openssl.cnf 

echo -e ${GREEN}generate CSR for client key
echo -e ${GRAY}
openssl req -out private/client_${CN}.csr -key private/client_${CN}.key -new -config openssl.cnf -subj "/C=US/ST=New Hampshire/CN=${CN}"

echo -e ${GREEN}sign the CSR
echo -e ${GRAY}
openssl x509 -req -in private/client_${CN}.csr -CA certs/ca.crt -CAkey private/ca.key -CAcreateserial -out certs/client_${CN}.crt -days 36525 

