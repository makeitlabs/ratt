# HTTPS Request Example with Client Certificates

Builds on the "04_https_request" example, adding client certificates and requiring validation of the server certificate.  This forms the basis of two-way authenticated, encrypted communications on the ESP32 platform.

This example turns a number of the formerly hardcoded settings into configuration settings, so running 'make menuconfig' is definitely recommended/necessary for success.

Included is a script to build a basic self-signed CA cert, server cert, and client cert.  See the 'certs' directory for more details.

Also, sample Apache site configs are included for both a simple static content directory as well as the MakeIt Labs Flask/WSGI authentication backend.  These configs are in the 'apache' directory.


As this is built off of an esp-idf example, see the README.md file in the upper level 'examples' directory in the esp-idf distribution for more information about examples.
