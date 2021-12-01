
# Developing and Testing on a Desktop Host

It's possible to run the RATT software on a development host, with simulated I/O, RFID, display and buttons.  This is a good way to develop and debug new features, before final testing on the actual hardware.  It makes for much shorter development interation cycles.

## Install prerequisites

These instructions are meant for Ubuntu 20.04 (LTS), typically run in a virtual machine.  They may work on future versions of Ubuntu, but this is not guaranteed.

Start by installing the following packages:

`sudo apt install python3-pyqt5 python3-pyqt5.qtmultimedia python3-pyqt5.qtserialport python3-pyqt5.qtquick qml-module-qtquick-controls qml-module-qtmultimedia python3-simplejson python3-paho-mqtt mosquitto`


## Set up certs

`cd ~/ratt/deployment/certs/mqtt`

`./gen_ca_and_server_certs.sh`

`./gen_client_cert.sh ubuntu`

`./deploy_mosquitto_certs.sh`

## Add alias in `/etc/hosts`

`127.0.1.1	ubuntu devel`

## Run MQTT broker (if desired)

`sudo mosquito &`

## Run the Authentication Backend

This requires a checkout of the 'authbackend' repository.

`cd ~/authbackend`
`python authserver.py`
# (See README.md in authbackend repo for more information)

## Run the app

The `ratt-devhost.ini` config file contains settings to allow the app
to run on the development host.

`cd ~/ratt/firmware/rpi/app`
`python3 ./main.py --ini ./ratt-devhost.ini`


