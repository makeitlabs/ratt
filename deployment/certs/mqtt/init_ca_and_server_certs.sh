#!/bin/bash

if [ ! -f .capassword ]; then
	echo "file .capassword must be created to contain CA password"
	exit 0
fi

GREEN='\033[1;32m'
GRAY='\033[0;37m'

if [ -d ssl ]; then
	echo "'ssl' directory already exists.  exiting."
	exit 0
fi

mkdir ssl
chmod 0700 ssl
cd ssl
mkdir certs private
ln -s ../openssl.cnf openssl.cnf

echo -e ${GREEN}generate CA cert and key...
echo -e ${GRAY}

openssl req -new -x509 -days 36525 -extensions v3_ca -keyout private/ca.key -out certs/ca.crt -config openssl.cnf -subj '/C=US/ST=New Hampshire/CN=ca' -passout file:../.capassword -verbose

#echo -e ${GREEN}generate server key with encryption
#echo -e ${GRAY}
#openssl genrsa -des3 -out private/server.key 2048 #-config openssl.cnf 

echo -e ${GREEN}generate server key without encryption...
echo -e ${GRAY}
openssl genrsa -out private/server.key 2048

echo -e ${GREEN}generate certificate signing request to send to the CA 
echo -e ${GRAY}
openssl req -out private/server.csr -key private/server.key -new -config openssl.cnf -subj '/C=US/ST=New Hampshire/CN=mqtt' -passin file:../.capassword -verbose

echo -e ${GREEN}sign the CSR with the CA key
echo -e ${GRAY}
openssl x509 -req -in private/server.csr -CA certs/ca.crt -CAkey private/ca.key -CAcreateserial -out certs/server.crt -days 36525 -passin file:../.capassword 

