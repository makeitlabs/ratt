#!/bin/sh

GREEN='\033[1;32m'
GRAY='\033[0;37m'

mkdir ssl
chmod 0700 ssl
cd ssl
mkdir certs private
cp ../openssl.cnf .

clear
echo -e ${GREEN}generate CA cert and key
echo -e ${GRAY}
openssl req -new -x509 -days 36525 -extensions v3_ca -keyout private/ca.key -out certs/ca.crt -config openssl.cnf -subj '/C=US/ST=New Hampshire/CN=ca'

#echo -e ${GREEN}generate server key with encryption
#echo -e ${GRAY}
#openssl genrsa -des3 -out private/server.key 2048 #-config openssl.cnf 

echo -e ${GREEN}generate server key without encryption
echo -e ${GRAY}
openssl genrsa -out private/server.key 2048 #-config openssl.cnf

echo -e ${GREEN}generate certificate signing request to send to the CA 
echo -e ${GRAY}
openssl req -out private/server.csr -key private/server.key -new -config openssl.cnf -subj '/C=US/ST=New Hampshire/CN=auth'

echo -e ${GREEN}sign the CSR with the CA key
echo -e ${GRAY}
openssl x509 -req -in private/server.csr -CA certs/ca.crt -CAkey private/ca.key -CAcreateserial -out certs/server.crt -days 36525 

