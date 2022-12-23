
# MQTT SSL/TLS

Some rough utilities to generate and deploy self-signed certificates for MQTT in RATT.

## Generating CA and server certs (self-signed)

Create a file `.capassword` with your CA password in it.

`./init_ca_and_server_certs.sh`

All certs will be created in the `ssl` directory.  Private keys and csr's will go into the `private` directory, and certs will go ino the `certs` directory.

## Deploying the CA and server certs to mosquitto broker

`./deploy_mosquitto_certs.sh`

This script will copy the certs and key files to the appropriate place in `/etc/mosquitto` ... Note that the paths are hardcoded, if you have your install located somewhere else, you'll need to fix the script.

This script also copies a config include into `/etc/mosquitto/conf.d` to enable SSL.

**This script will stop and start the mosquitto broker service!**

## Generating a client cert

`./gen_client_cert.sh [CN]`

To generate a client cert, you must supply the CN for the client on the command line.  For RATT, we intend to use the MAC address of the node for the CN (all lowercase, no colons).

## Regenerating client certs from a list

The file `ssl/clients` is populated with the CN of each created client.  You can pre-populate this file and run `./regen-client-certs.sh` to rebuild all certs.  This is useful if you need to redeploy all certs.  Note that it will not overwrite certs that have already been made.

## Deploying MQTT certificates to the auth backend (deprecated)

_This is now deprecated as the auth backend runs in a separate container._

The authbackend needs valid client certificates so it can connect to the MQTT broker.  Generate the client cert named `authbackend` using the script, and then deploy it with the included script:

`./deploy_authbackend_certs.sh`

This will deploy the certs to both the production and staging servers, and, importantly, it will restart the Apache webserver, so be aware before you do this.

## Deploying MQTT certificates to Node-RED

Node-RED is used for automation glue and "smarts" for the RATT system (e.g. Slack integration).  Generate client certs with the name `nodered' and upload the certs into Node-RED TLS config for MQTT.

## Deploying certificates to a RATT node

To deploy to a RATT node you will need to have a working `fab` configuration, including `ssh-config` and properly deployed SSH keys.  It is beyond the scope of this document (for now) to help you get that configured.

You can test your `fab` config as follows:

`fab --hosts=[IP] test`

If all is well, you should get a similar result (exact `uname` string does not matter, just that the command executed):
`Linux raspberrypi0-wifi 4.14.79 #1 Wed Nov 14 01:55:54 UTC 2018 armv6l armv6l armv6l GNU/Linux`

Once that is working, you can deploy the client cert you just generated using the following command:

`fab --hosts=[IP] deploy-certs --cn=[CN]`

This will copy the certs and keys over and spit out some info about each to give some confidence that they are correct.

## Restarting the app and testing

If you were running the app automatically via systemctl then you can restart it through `fab` with the following command:

`fab --hosts=[IP] restart-app`

Once restarted, it should use the new certs/keys and be able to connect to the MQTT broker and you should see it spit out messages.  It's helpful to use `mosquitto_sub` on the broker host for testing.

First generate a certificate for testing,

`./gen_client_cert.sh test`

To start a debug session (note you need to supply a broker hostname that matches the server cert):

`mosquitto_sub --cafile ssl/certs/ca.crt --cert ssl/certs/client_test.crt --key ssl/private/client_test.key -t ratt/status/node# -v -h [broker hostname]`
