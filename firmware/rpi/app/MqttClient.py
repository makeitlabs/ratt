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

from PyQt5.QtCore import Qt, QThread, QWaitCondition, QMutex, QTimer, pyqtSignal, pyqtSlot, pyqtProperty
import paho.mqtt.client as mqtt
from Logger import Logger

class MqttClient(QThread):
    TOPIC_BROADCAST_CONTROL = 'control/broadcast'
    TOPIC_TARGETED_CONTROL = 'control/node'
    TOPIC_TARGETED_STATUS = 'status/node'

    Disconnected = 0
    Connecting = 1
    Reconnecting = 2
    Connected = 3

    MQTT_3_1 = mqtt.MQTTv31
    MQTT_3_1_1 = mqtt.MQTTv311

    connected = pyqtSignal()
    disconnected = pyqtSignal()

    stateChanged = pyqtSignal(int)
    hostnameChanged = pyqtSignal(str)
    portChanged = pyqtSignal(int)
    keepAliveChanged = pyqtSignal(int)
    cleanSessionChanged = pyqtSignal(bool)
    protocolVersionChanged = pyqtSignal(int)

    broadcastEvent = pyqtSignal(str,str)
    targetedEvent = pyqtSignal(str,str)
    brokerConnectionEvent = pyqtSignal(bool)

    def __init__(self, loglevel='WARNING', baseTopic='ratt'):
        QThread.__init__(self)

        self.logger = Logger(name='ratt.mqtt')
        self.logger.setLogLevelStr(loglevel)
        self.debug = self.logger.isDebug()

        self._quit = False
        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self._node_id = None
        self._hostname = 'localhost'
        self._port = 1883
        self._keepalive = 60
        self._clean_session = True
        self._protocol_version = MqttClient.MQTT_3_1

        self._reconnect_time = 10000

        self._state = MqttClient.Disconnected
        self._base_topic = baseTopic

    def init_client(self, hostname='localhost', port=1883, nodeId='', reconnectTime=60,
                    sslEnabled = False, caCertFile = '', clientCertFile = '', clientKeyFile = ''):

        self._node_id = nodeId

        self._hostname = hostname
        self._port = port
        self._keepalive = 60
        self._reconnect_time = reconnectTime

        self._client = mqtt.Client(clean_session=self._clean_session, protocol=self.protocolVersion)
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message
        self._client.on_disconnect = self.on_disconnect
        self._client.on_log = self.on_log

        if sslEnabled:
            try:
                self.logger.info('SSL enabled, ca_cert=' + caCertFile + ' cert=' + clientCertFile + ' key=' + clientKeyFile)
                self._client.tls_set(ca_certs=caCertFile,
                                     certfile=clientCertFile,
                                     keyfile=clientKeyFile)
            except IOError:
                self.logger.error('Error loading SSL certificates!  Are the paths and filenames correct in the .ini file?')
            except:
                self.logger.error('Unknown error loading SSL certificates.')

        self.logger.info('MQTT client initialized, broker host is ' + self._hostname + ':' + str(self._port))
        self.connectToBroker()

    @pyqtProperty(int, notify=stateChanged)
    def state(self):
        return self._state

    @state.setter
    def state(self, state):
        if self._state == state: return
        self._state = state
        self.stateChanged.emit(state)

    @pyqtProperty(str, notify=hostnameChanged)
    def hostname(self):
        return self._hostname

    @hostname.setter
    def hostname(self, hostname):
        if self._hostname == hostname: return
        self._hostname = hostname
        self.hostnameChanged.emit(hostname)

    @pyqtProperty(int, notify=portChanged)
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        if self._port == port: return
        self._port = port
        self.portChanged.emit(port)

    @pyqtProperty(int, notify=keepAliveChanged)
    def keepAlive(self):
        return self._keepalive

    @keepAlive.setter
    def keepAlive(self, keepAlive):
        if self._keepalive == keepAlive: return
        self._keepalive = keepAlive
        self.keepAliveChanged.emit(keepAlive)

    @pyqtProperty(bool, notify=cleanSessionChanged)
    def cleanSession(self):
        return self._clean_session

    @cleanSession.setter
    def cleanSession(self, cleanSession):
        if self._clean_session == cleanSession: return
        self._clean_session = cleanSession
        self.cleanSessionChanged.emit(cleanSession)

    @pyqtProperty(int, notify=protocolVersionChanged)
    def protocolVersion(self):
        return self._protocol_version

    @protocolVersion.setter
    def protocolVersion(self, protocolVersion):
        if self._protocol_version == protocolVersion: return
        if protocolVersion in (MqttClient.MQTT_3_1, MQTT_3_1_1):
            self._protocol_version = protocolVersion
            self.protocolVersionChanged.emit(protocolVersion)

    def publish(self, topic=None, subtopic=None, msg=None, qos=2, retain=False):
        # "subtopic" is a shortcut way of not having to supply the prefix part of the topic
        # for RATT; generally all messages should be published with this prefix
        if self._node_id is not None:
            if topic is None and subtopic is not None:
                t = self._base_topic + '/' + MqttClient.TOPIC_TARGETED_STATUS + '/' + self._node_id + '/' + subtopic
            else:
                t = topic

            self._client.publish(t, payload=msg, qos=qos, retain=retain)

    @pyqtSlot(str, str)
    def slotPublishSubtopic(self, subtopic, msg):
        self.publish(subtopic=subtopic, msg=msg)


    #################################################################
    @pyqtSlot()
    def connectToBroker(self):
        if not self.isRunning():
            self.start();
        else:
            self.cond.wakeOne();

    def run(self):
        self.logger.info("thread run")
        while not self._quit:

            if self.state is MqttClient.Disconnected and self._hostname:
                try:
                    self.logger.info('client connecting to ' + self._hostname + ':' + str(self._port))
                    self.state = MqttClient.Connecting
                    self._client.reconnect_delay_set(min_delay=1, max_delay=30)
                    self._client.connect(self._hostname, port=self._port, keepalive=self._keepalive)
                except:
                    self.logger.info('could not connect, retrying in ' + str(self._reconnect_time / 1000) + ' seconds')
                    self.state = MqttClient.Disconnected
                    self.msleep(self._reconnect_time)

                self.msleep(self._reconnect_time)

            self._client.loop(timeout=1.0)


        self.logger.info("thread done")

    @pyqtSlot()
    def disconnectFromBroker(self):
        self._client.disconnect()

    def subscribe(self, topic):
        if self.state == MqttClient.Connected:
            self.logger.info('subscribe topic=' + topic)
            self._client.subscribe(topic)

    def on_log(self, client, userdata, level, buf):
        if level == mqtt.MQTT_LOG_ERR:
            f = self.logger.error
        elif level == mqtt.MQTT_LOG_WARNING:
            f = self.logger.warning
        elif level == mqtt.MQTT_LOG_NOTICE:
            f = self.logger.info
        elif level == mqtt.MQTT_LOG_INFO:
            f = self.logger.info
        else:
            f = self.logger.debug

        f(buf)

    def on_connect(self, client, userdata, flags, rc):
        if self._node_id is not None:
            self.state = MqttClient.Connected
            self.logger.info('on_connect')
            self.subscribe(self._base_topic + '/' + MqttClient.TOPIC_BROADCAST_CONTROL + '/#')
            self.subscribe(self._base_topic + '/' + MqttClient.TOPIC_TARGETED_CONTROL + '/' + self._node_id + '/#')
            self.brokerConnectionEvent.emit(True)

    def on_disconnect(self, client, userdata, rc):
        self.state = MqttClient.Disconnected
        self.logger.info('on_disconnect')
        self.brokerConnectionEvent.emit(False)

    def on_message(self, client, userdata, message):
        if self._node_id is not None:
            topic_broadcast = self._base_topic + '/' + MqttClient.TOPIC_BROADCAST_CONTROL + '/'
            topic_targeted = self._base_topic + '/' + MqttClient.TOPIC_TARGETED_CONTROL + '/' + self._node_id + '/'

            self.logger.info('on_message: ' + message.topic + ' -> ' + message.payload)
            if message.topic.startswith(topic_broadcast):
                subtopic = message.topic.replace(topic_broadcast, '')
                self.broadcastEvent.emit(subtopic, message.payload)
            elif message.topic.startswith(topic_targeted):
                subtopic = message.topic.replace(topic_targeted, '')
                self.targetedEvent.emit(subtopic, message.payload)
