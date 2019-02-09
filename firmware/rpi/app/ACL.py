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

from PyQt5.QtCore import Qt, QObject, QUrl, QIODevice, QByteArray, QDateTime, QMutex, pyqtSignal, pyqtSlot, pyqtProperty
from PyQt5.QtCore import QFile, QFileInfo
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from Logger import Logger
import logging
import hashlib
import simplejson as json
import time
from CachedRemoteFile import CachedRemoteFile

class ACL(CachedRemoteFile):
    recordUpdate = pyqtSignal()

    @pyqtProperty(int, notify=recordUpdate)
    def numRecords(self):
        self.mutex.lock()
        n = self._numRecords
        self.mutex.unlock()
        return n

    @pyqtProperty(int, notify=recordUpdate)
    def numActiveRecords(self):
        self.mutex.lock()
        n = self._numActiveRecords
        self.mutex.unlock()
        return n

    @pyqtSlot()
    def slotUpdate(self):
        self.recordUpdate.emit()

    def __init__(self, loglevel='WARNING', netWorker = None, mqtt = None, url = '', cacheFile = None):
        CachedRemoteFile.__init__(self)
        self.logger = Logger(name='ratt.acl')
        self.logger.setLogLevelStr('INFO')
        self.debug = self.logger.isDebug()

        self._numRecords = 0
        self._numActiveRecords = 0

        self.setup(logger=self.logger, netWorker=netWorker, url=url, cacheFile=cacheFile)


        self.mqtt = mqtt
        self.mqtt.broadcastEvent.connect(self.__slotBroadcastMQTTEvent)
        self.mqtt.targetedEvent.connect(self.__slotTargetedMQTTEvent)

        self.update.connect(self.slotUpdate)

    def search(self, hash):
        self.mutex.lock()
        found_record = []

        for record in self._obj:
            if record['tagid'] == hash:
                found_record = record
                break

        self.mutex.unlock()
        return found_record

    def countActive(self, j):
        active = 0
        for record in j:
            if record['allowed'] == 'allowed':
                active = active + 1
        return active

    # this hook is called just after parsing but before hashes are checked
    # the mutex is not held at this point
    def parseJSON__hook_unlocked(self, parsed):
        o = {}
        o['count'] = len(parsed)
        o['active'] = self.countActive(parsed)
        return o

    # this hook is called if the hashes differ, and the mutex IS held
    def parseJSON__hook_locked(self, o):
        self._numRecords = o['count']
        self._numActiveRecords = o['active']
        self.logger.info('updated ACL with %d entries, %d active, hash=%s' % (self._numRecords, self._numActiveRecords, self._hash))

    # MQTT targeted event
    @pyqtSlot(str, str)
    def __slotTargetedMQTTEvent(self, subtopic, message):
        tsplit = subtopic.split('/')

        if len(tsplit) >= 2 and tsplit[0] == 'acl':
            cmd = tsplit[1]

            if cmd == 'update':
                self.download()

    # MQTT broadcast event
    @pyqtSlot(str, str)
    def __slotBroadcastMQTTEvent(self, subtopic, message):
        tsplit = subtopic.split('/')

        if len(tsplit) >= 2 and tsplit[0] == 'acl':
            cmd = tsplit[1]

            if cmd == 'update':
                self.download()
