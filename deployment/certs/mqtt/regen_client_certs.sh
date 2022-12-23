#!/bin/bash

RED='\033[1;31m'
GREEN='\033[1;32m'
CYAN='\033[1;36m'
GRAY='\033[0;37m'
WHITE='\033[1;37m'


if [ ! -d ssl ]; then
	echo -e "${RED}ssl directory doesn't exist yet.  did you initialize the ca and server?"
	echo -e ${GRAY}
	exit 0
fi


if [ ! -f ssl/clients ]; then
	echo -e "${RED}no clients file, can't regenerate${GRAY}"
	exit 0
fi

clients=$(cat ssl/clients)

for client in $clients
do
	./gen_client_cert.sh $client
done

