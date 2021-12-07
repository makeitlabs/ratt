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

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QVariant, QEvent, Qt, QCoreApplication, QUrl
from PyQt5 import QtCore
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from PyQt5.QtGui import QKeyEvent
from RattConfig import RattConfig
from NetWorker import NetWorker
from ACL import ACL
from MqttClient import MqttClient
from RFID import RFID
from Logger import Logger
import sys
import subprocess
import argparse

class RattAppEngine(QQmlApplicationEngine):
    restart = pyqtSignal()

    def __init__(self):
        QQmlApplicationEngine.__init__(self)

        parser = argparse.ArgumentParser(description='RATT Application (Personality state machine and GUI).')
        parser.add_argument('--ini', dest='inifile', default='/data/ratt/ratt.ini', help='path to .ini file e.g. /tmp/ratt-test.ini, default is /data/ratt/ratt.ini')

        args = parser.parse_args()

        # Name of the Mender artifact
        self.mender_artifact = 'unknown'

        # load the config
        self.config = RattConfig(inifile=args.inifile, loglevel='DEBUG')

        self.config.configChanged.connect(self.slotConfigChanged)
        self.config.configError.connect(self.slotConfigError)

        # create parent logger which will optionally log to file and console, and opionally enable Qt logging
        self.logger = Logger(name='ratt',
                             filename=self.config.value('Log.File'), stream=self.config.value('Log.Console'),
                             qt=self.config.value('Log.Qt'), qtVerbose=self.config.value('Log.QtVerbose'))
        self.logger.setLogLevelStr(self.config.value('Log.LogLevel'))
        self.logger.info('Initializing RATT System')
        self.debug = self.logger.isDebug()

        self.__bootstrapSystem__()


    def __setContextProperties__(self, reinit = False):
        # create context properties so certain objects can be accessed from QML
        if not reinit:
            self.rootContext().setContextProperty("appEngine", self)
            self.rootContext().setContextProperty("logger", self.logger)
            self.rootContext().setContextProperty("config", self.config)
            self.rootContext().setContextProperty("netWorker", self._netWorker)
            self.rootContext().setContextProperty("acl", self._acl)
            self.rootContext().setContextProperty("rfid", self._rfid)
            self.rootContext().setContextProperty("mqtt", self.mqtt)
            self.rootContext().setContextProperty("menderArtifact", self.mender_artifact)

        self.rootContext().setContextProperty("personality", self.personality)

    def __startSystem__(self):
        # initialize the node personality and the other necessary modules
        self.__initSystem__()
        self.__initPersonality__()

        self.__setContextProperties__()

        # temporary for test; will move somewhere else eventually
        self._acl.download()

        # begin executing the personality state machine
        self.personality.execute()
        self.load("main.qml")


    @pyqtSlot()
    def slotConfigChanged(self):
        if self.config.haveInitialRemoteConfig:
            self.logger.info('CONFIG CHANGED - RE-INIT')

            #robjs = self.rootObjects()
            #if robjs is not None:
            #    for ro in robjs:
            #        ro.close()

            self.exit.emit(0)
        else:
            self.__startSystem__()

    @pyqtSlot()
    def slotConfigError(self):
        self.__startSystem__()

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

    def __bootstrapSystem__(self):
        # MQTT module, for publishing and subscribing to the MQTT broker
        self._mqtt = MqttClient(loglevel=self.config.value('MQTT.LogLevel'),
                                baseTopic=self.config.value('MQTT.BaseTopic'))

        # NetWorker handles fetching and maintaining ACLs, configs, and other network functions
        self._netWorker = NetWorker(loglevel=self.config.value('Auth.LogLevel'),
                                    ifcName=self.config.value('General.NetworkInterfaceName'),
                                    nodeId=self.config.value('General.NodeId'),
                                    mqtt=self._mqtt)

        self._netWorker.setSSLClientCertConfig(enabled=self.config.value('HTTPS.ClientCertsEnabled'),
                                               caCertFile=self.config.value('HTTPS.CaCertFile'),
                                               clientCertFile=self.config.value('HTTPS.ClientCertFile'),
                                               clientKeyFile=self.config.value('HTTPS.ClientKeyFile'))

        self._netWorker.setAuth(user=self.config.value('Auth.HttpAuthUser'),
                                password=self.config.value('Auth.HttpAuthPassword'))

        # setting the netWorker in the config module will trigger the load of the second stage config (remote)
        self.config.setNetWorker(netWorker=self._netWorker)

        # set the mqtt object for the config engine, this allows triggering of config reloads
        self.config.setMQTT(mqtt=self._mqtt)


    def __initSystem__(self):
        # try to read mender artifact name from filesystem.  this is the version of the base system that is running.
        try:
            with open('/etc/mender/artifact_info') as f:
                for line in f:
                    (k,v) = line.split('=')
                    if k == 'artifact_name':
                        self.mender_artifact = v
        except:
            pass

        # Access Control List module, for maintaining the database of allowed users for this resource
        self._acl = ACL(loglevel=self.config.value('Auth.LogLevel'),
                        netWorker=self._netWorker,
                        mqtt=self._mqtt,
                        url=self.config.value('Auth.AclUrl'),
                        cacheFile=self.config.value('Auth.AclCacheFile'))

        # RFID reader
        self._rfid = RFID(portName=self.config.value('RFID.SerialPort'),
                          loglevel=self.config.value('RFID.LogLevel'))
        self._rfid.monitor()

        # Initialize and connect MQTT client
        nid = self.config.value('General.NodeId')
        if nid is None:
            nid = self._netWorker.currentNodeId

        self._mqtt.init_client(hostname=self.config.value('MQTT.BrokerHost'),
                               port=self.config.value('MQTT.BrokerPort'),
                               reconnectTime=self.config.value('MQTT.ReconnectTime'),
                               nodeId=nid,
                               sslEnabled=self.config.value('MQTT.SSLEnabled'),
                               caCertFile=self.config.value('MQTT.CACertFile'),
                               clientCertFile=self.config.value('MQTT.ClientCertFile'),
                               clientKeyFile=self.config.value('MQTT.ClientKeyFile'))


    def shutdown(self):
        self.logger.info('Shutting down.')

        # de-init the personality
        self.personality.deinit()

        # stop raspi2fb
        subprocess.run(['systemctl', 'stop', 'raspi2fb'])

        # shut down system
        subprocess.run(['/sbin/shutdown', '-h', 'now'])

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
    def mqtt(self):
        return self._mqtt


    @pyqtSlot(int, bool)
    def syntheticKeypressHandler(self, keycode, pressed):
        evt = QKeyEvent(QEvent.KeyPress if pressed else QEvent.KeyRelease, keycode, Qt.NoModifier)
        objs = self.rootObjects()
        if len(objs) == 1:
            QCoreApplication.postEvent(objs[0], evt)
