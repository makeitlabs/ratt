#!/bin/bash

RED='\033[1;31m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
GRAY='\033[0;37m'
WHITE='\033[1;37m'

if [ ! -d ssl ]; then
	echo -e "${RED}ssl directory doesn't exist yet.  did you initialize the ca and server?${GRAY}"
	exit 1
fi

CN=$1

if [ -z $CN ]; then
    echo -e "${RED}Must pass CN for client on command line - typically the lowercase mac addr without colons for ratt/uratt${GRAY}"
    exit 2
else
    echo -e "${WHITE}CN is ${CYAN}${CN}${GRAY}"
fi

cd ssl

if [ -f private/client_${CN}.key ] || [ -f private/client_${CN}.csr ] || [ -f certs/client/${CN}.crt ]; then
	echo -e "${RED}Key, CSR or cert for $CN already exists.  Not generating.${GRAY}"
	exit 3
fi

echo -e ${GREEN}generate client key without encryption...
echo -e ${GRAY}
openssl genrsa -out private/client_${CN}.key 2048 

echo -e ${GREEN}generate CSR for client key...
echo -e ${GRAY}
openssl req -out private/client_${CN}.csr -key private/client_${CN}.key -new -config openssl.cnf -subj "/C=US/ST=New Hampshire/CN=${CN}" -passin file:../.capassword

echo -e ${GREEN}sign the CSR...
echo -e ${GRAY}
openssl x509 -req -in private/client_${CN}.csr -CA certs/ca.crt -CAkey private/ca.key -CAcreateserial -out certs/client_${CN}.crt -days 36525 -passin file:../.capassword

if [ ! -f clients ]; then
	echo -e ${GREEN}create clients file...
	echo -e ${GRAY}
	touch clients
fi

grep $CN clients
if [ $? = 1 ]; then
	echo -e ${GREEN}add $CN to clients file.
	echo -e ${GRAY}
	echo $CN >> clients
else
	echo -e ${GREEN}$CN is already in clients file.
	echo -e ${GRAY}
fi
