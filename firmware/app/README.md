
# Developing and Testing on a Desktop Host

It's possible to run the RATT software on a development host, with simulated I/O, RFID, display and buttons.  This is a good way to develop and debug new features, before final testing on the actual hardware.  It makes for much shorter development interation cycles.

## Install prerequisites

These instructions are meant for Ubuntu 20.04 (LTS), typically run in a virtual machine.  They may work on future versions of Ubuntu, but this is not guaranteed.

Start by installing the following packages:

    sudo apt install python3-pyqt5 python3-pyqt5.qtmultimedia python3-pyqt5.qtserialport python3-pyqt5.qtquick qml-module-qtquick-controls qml-module-qtmultimedia python3-paho-mqtt mosquitto

These packages are needed to run the application (Python3 + PyQt5 + QML), as well as the optional backend services such as the Mosquitto MQTT broker.

## Set up Certificates

### Local Self-Signed Certs

For running completely contained on a development host, you will need to create your own CA, server and client certificates.  The certificates are used for the MQTT client in RATT to connect to the MQTT broker (aka server).

You can create development certs as follows:

    cd ~/ratt/deployment/certs/mqtt

    ./gen_ca_and_server_certs.sh
    ./gen_client_cert.sh ubuntu
    ./deploy_mosquitto_certs.sh

### Production Certs

It is also possible to use real MQTT certificates from a production server.  In this case, the CA and server certs will have already been created.  A script is usually used to create new certificates, similar to above.

  * Create a client cert on the production server
  * Copy CA cert and private certs and keys to your development server
  * Edit the RATT config file and set the SSL certificate options to point to your certs

## Add host alias in `/etc/hosts`

Note that the localhost alias hostname 'ubuntu' must match the name used when the client cert was generated in the previous step, otherwise the CN will not match and there will be an SSL error.

    127.0.1.1	ubuntu devel

## MQTT Broker

### Local MQTT

To run a development MQTT broker locally, if a `systemd` service was not installed.

    sudo mosquito &

### Remote/Production MQTT via SSH Tunnel

It is also possible to use the production MQTT server with SSH tunneling.  This is especially useful when developing features which interact with backend automation.  The RATT config must be edited to point to a localhost tunneled port for the MQTT broker, and the SSH tunnel must be established.

## Authentication Backend

### Local Auth Backend

Running the auth backend locally requires a clone of the `authbackend` repository and proper configuration.  See `README.md` in the repo for more information about configuration of databases and ini files.

    cd ~/authbackend
    python authserver.py

### Remote/Production Auth Backend

It is also possible to use a remote auth backend, either directly accessible via a public address or through an SSH tunnel.  The RATT config file must be edited to use the correct server address, port, API path, and API credentials.

## Run the RATT Application

The `ratt-devhost.ini` config file contains appropriate settings to allow the app to run on the development host with simulated I/O, RFID, and diagnostics display output.

    cd ~/ratt/firmware/rpi/app
    python3 ./main.py --ini ./ratt-devhost.ini
