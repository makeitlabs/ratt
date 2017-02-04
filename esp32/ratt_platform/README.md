# HTTPS Request Example with Client Certificates and HTTP/HTTPS library

Builds on the "04_https_request" example, adding client certificates and requiring validation of the server certificate.  This forms the basis of two-way authenticated, encrypted communications on the ESP32 platform.

Now incorporates a port of HISONA's HTTP/HTTPS REST client C library, adapted for ESP32 platform quirks and extended to support client certs, and http basic auth.  See https://github.com/HISONA/https_client for original code.


This example turns a number of the formerly hardcoded settings into configuration settings, so running 'make menuconfig' is definitely recommended/necessary for success.

Included is a script to build a basic self-signed CA cert, server cert, and client cert.  See the 'certs' directory for more details.

Also, sample Apache site configs are included for both a simple static content directory as well as the MakeIt Labs Flask/WSGI authentication backend.  These configs are in the 'apache' directory.


As this is built off of an esp-idf example, see the README.md file in the upper level 'examples' directory in the esp-idf distribution for more information about examples.

Note: until ESP-IDF is fixed, a patch is required in mbedtls component code to fix a build issue:
See https://github.com/ARMmbed/mbedtls/commit/7247f99b3e068a2b90b7776a2cdd438fddb7a38b
