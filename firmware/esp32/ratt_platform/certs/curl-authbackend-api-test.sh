#!/bin/sh

curl -vv --cacert ssl/server-cert.pem --cert ssl/client-cert-curl.pem:sekrit https://192.168.0.1/auth/api/v1/resources/frontdoor/acl -u foo:bar



