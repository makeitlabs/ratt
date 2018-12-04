# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
#  _____       ______________
# |  __ \   /\|__   ____   __|
# | |__) | /  \  | |    | |
# |  _  / / /\ \ | |    | |
# | | \ \/ ____ \| |    | |
# |_|  \_\/    \_\_|    |_|    ... RFID ALL THE THINGS!
#
# A resource access control and telemetry solution for Makerspaces
#
# Developed at MakeIt Labs - New Hampshire's First & Largest Makerspace
# http://www.makeitlabs.com/
#
# Copyright 2018 MakeIt Labs
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# --------------------------------------------------------------------------
#
# Author: Steve Richardson (steve.richardson@makeitlabs.com)
#

#!/usr/bin/python

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QVariant, QEvent, Qt, QCoreApplication
from PyQt5 import QtCore
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt5.QtGui import QKeyEvent
from RattConfig import RattConfig
from NetWorker import NetWorker
from ACL import ACL
from Telemetry import Telemetry
from MqttClient import MqttClient
from RFID import RFID
from Logger import Logger
import sys
import argparse
from commands import getoutput

class RattAppEngine(QQmlApplicationEngine):
    def __init__(self):
        QQmlApplicationEngine.__init__(self)

        parser = argparse.ArgumentParser(description='RATT Application (Personality state machine and GUI).')
        parser.add_argument('--ini', dest='inifile', default='/data/ratt/ratt.ini', help='path to .ini file e.g. /tmp/ratt-test.ini, default is /data/ratt/ratt.ini')

        args = parser.parse_args()

        # load the config
        self.config = RattConfig(inifile=args.inifile)

        # create parent logger which will optionally log to file and console, and opionally enable Qt logging
        self.logger = Logger(name='ratt',
                             filename=self.config.value('Log.File'), stream=self.config.value('Log.Console'),
                             qt=self.config.value('Log.Qt'), qtVerbose=self.config.value('Log.QtVerbose'))
        self.logger.setLogLevelStr(self.config.value('Log.LogLevel'))
        self.logger.info('Initializing RATT System')
        self.debug = self.logger.isDebug()

        # initialize the node personality and the other necessary modules
        self.__initSystem__()
        self.__initPersonality__()

        # create context properties so certain objects can be accessed from QML
        self.rootContext().setContextProperty("appEngine", self)
        self.rootContext().setContextProperty("config", self.config)
        self.rootContext().setContextProperty("personality", self.personality)
        self.rootContext().setContextProperty("netWorker", self._netWorker)
        self.rootContext().setContextProperty("acl", self._acl)
        self.rootContext().setContextProperty("rfid", self._rfid)
        self.rootContext().setContextProperty("mqtt", self.mqtt)

        # temporary for test; will move somewhere else eventually
        self._acl.download()

        # begin executing the personality state machine
        self.personality.execute()


    def __initPersonality__(self):
        # dynamically import and instantiate the correct 'Personality' class, which contains the specific logic
        # implementation for a given tool
        personalityClass = 'Personality' + self.config.value('Personality.Class')

        try:
            sys.path.append('personalities')
            module = __import__(personalityClass)

            self.personality = module.Personality(loglevel=self.config.value('Personality.LogLevel'), app=self)
        except:
            self.logger.exception('could not establish personality: ' + personalityClass)
            exit(-1)


    def __initSystem__(self):
        # MQTT module, for publishing and subscribing to the MQTT broker
        self._mqtt = MqttClient(loglevel=self.config.value('MQTT.LogLevel'),
                                baseTopic=self.config.value('MQTT.BaseTopic'))

        # NetWorker handles fetching and maintaining ACLs, logging, and other network functions
        self._netWorker = NetWorker(loglevel=self.config.value('Auth.LogLevel'),
                                    mqtt=self._mqtt)

        self._netWorker.setSSLCertConfig(enabled=self.config.value('SSL.Enabled'),
                                         caCertFile=self.config.value('SSL.CaCertFile'),
                                         clientCertFile=self.config.value('SSL.ClientCertFile'),
                                         clientKeyFile=self.config.value('SSL.ClientKeyFile'))

        self._netWorker.setAuth(user=self.config.value('Auth.HttpAuthUser'),
                                password=self.config.value('Auth.HttpAuthPassword'))

        # Access Control List module, for maintaining the database of allowed users for this resource
        self._acl = ACL(loglevel=self.config.value('Auth.LogLevel'),
                        netWorker=self._netWorker,
                        mqtt=self._mqtt,
                        url=self.config.value('Auth.AclUrl'),
                        cacheFile=self.config.value('Auth.AclCacheFile'))



        # telemetry module, for collecting and posting events back to the auth server
        self._telemetry = Telemetry(loglevel=self.config.value('Telemetry.LogLevel'),
                                    netWorker=self._netWorker,
                                    mqtt=self._mqtt,
                                    url=self.config.value('Telemetry.EventUrl'),
                                    cacheFile=self.config.value('Telemetry.EventCacheFile'))

        # RFID reader
        self._rfid = RFID(portName=self.config.value('RFID.SerialPort'),
                          loglevel=self.config.value('RFID.LogLevel'))
        self._rfid.monitor()

        # Initialize and connect MQTT client
        self._mqtt.init_client(hostname=self.config.value('MQTT.BrokerHost'),
                               port=self.config.value('MQTT.BrokerPort'),
                               reconnectTime=self.config.value('MQTT.ReconnectTime'),
                               nodeId=self._netWorker.currentHwAddr.lower().replace(':', ''),
                               sslEnabled=self.config.value('SSL.Enabled'),
                               caCertFile=self.config.value('SSL.CaCertFile'),
                               clientCertFile=self.config.value('SSL.ClientCertFile'),
                               clientKeyFile=self.config.value('SSL.ClientKeyFile'))





    def shutdown(self):
        self.logger.info('Shutting down.')

        # de-init the personality
        self.personality.deinit()

        # stop raspi2fb
        getoutput('systemctl stop raspi2fb')

        # shut down system
        getoutput('/sbin/shutdown -h now')

        self.quit.emit()

    @property
    def rfid(self):
        return self._rfid

    @property
    def netWorker(self):
        return self._netWorker

    @property
    def acl(self):
        return self._acl

    @property
    def telemetry(self):
        return self._telemetry

    @property
    def mqtt(self):
        return self._mqtt


    @pyqtSlot(int, bool)
    def syntheticKeypressHandler(self, keycode, pressed):
        evt = QKeyEvent(QEvent.KeyPress if pressed else QEvent.KeyRelease, keycode, Qt.NoModifier)
        objs = self.rootObjects()
        if len(objs) == 1:
            QCoreApplication.postEvent(objs[0], evt)


