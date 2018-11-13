#!/bin/sh
mkdir ssl
chmod 0700 ssl
cd ssl
mkdir certs private
echo '100001' > serial
touch certindex.txt
cp ../openssl.cnf .

# create root cert
# This script will create private/cakey.pem  that is the private key of the CA and the cacert.pem that
# is the  which is the one you can give to others for import in their browsers.
clear
echo Creating CA key...
openssl req -new -x509 -extensions v3_ca -keyout private/cakey.pem -out cacert.pem -days 365 -config ./openssl.cnf

# Create a key and signing request for the server
# The output of this script is server-req.pem that is the CSR and the private/server-key.pem that is
# the private key
clear
echo Creating server key...
openssl req -new -nodes -out server-req.pem -keyout private/server-key.pem -days 365 -config ./openssl.cnf

# Sign the request
# This will produce server-cert.pem that is the public certificate
clear
echo Signing Request...
openssl ca -out server-cert.pem -days 365 -config ./openssl.cnf -infiles server-req.pem

### create client cert

# Create a key and signing request for each client
clear
echo Creating client key...
echo **************************************************************
echo NOTE: specify a different name than the CA for the common name
echo **************************************************************
openssl req -new -nodes -out client-req.pem -keyout private/client-key.pem -days 365 -config ./openssl.cnf

# Sign each request
clear
echo Signing Request...
openssl ca -out client-cert.pem -days 365 -config ./openssl.cnf -infiles client-req.pem

# Create the PKCS12 file
echo Generating PKCS12 file...
openssl pkcs12 -export -in client-cert.pem -inkey private/client-key.pem -certfile cacert.pem -name "client" -out client-cert.p12 -passout pass:client

# make curl compatible client cert
echo Generating curl-compatible PEM client cert
openssl pkcs12 -in client-cert.p12 -out client-cert-curl.pem -clcerts -passin pass:client -passout pass:sekrit

echo "Copying certs and key to build directory..."

# copy CA certificate into build directory
cp cacert.pem ../../main/cacert.pem

# copy client certificate into build directory
cp client-cert.pem ../../main/client_cert.pem

# copy client private key into build directory
cp private/client-key.pem ../../main/client_key.pem

