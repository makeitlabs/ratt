
Testing on Development Host
===========================

## Install prerequisites

`sudo apt install python-pyqt5 python-pyqt5.qtmultimedia python-pyqt5.qtserialport python-pyqt5.qtquick qml-module-qtquick-controls qml-module-qtmultimedia python-simplejson python-paho-mqtt mosquitto`

## Set up certs

`cd ~/ratt/deployment/certs/mqtt`

`./gen_ca_and_server_certs.sh`

`./gen_client_cert.sh ubuntu`

`./deploy_mosquitto_certs.sh`

## Add alias in `/etc/hosts`

`127.0.1.1	ubuntu devel`

## Run the app

The `ratt-devhost.ini` config file contains settings to allow the app
to run on the development host.

`./main.py --ini ./ratt-devhost.ini`


