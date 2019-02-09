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

class ACL(QObject):
    updateError = pyqtSignal(name='updateError')
    update = pyqtSignal()
    downloadActiveUpdate = pyqtSignal()

    @pyqtProperty(str, notify=update)
    def hash(self):
        self.mutex.lock()
        h = self._hash
        self.mutex.unlock()
        return h

    @pyqtProperty(int, notify=update)
    def numRecords(self):
        self.mutex.lock()
        n = self._numRecords
        self.mutex.unlock()
        return n

    @pyqtProperty(int, notify=update)
    def numActiveRecords(self):
        self.mutex.lock()
        n = self._numActiveRecords
        self.mutex.unlock()
        return n

    @pyqtProperty(str, notify=update)
    def date(self):
        self.mutex.lock()
        d = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._date))
        self.mutex.unlock()
        return d

    @pyqtProperty(str, notify=update)
    def status(self):
        self.mutex.lock()
        s = self._status
        self.mutex.unlock()
        return s

    @pyqtProperty(bool, notify=downloadActiveUpdate)
    def downloadActive(self):
        self.mutex.lock()
        isdl = self._downloadActive
        self.mutex.unlock()
        return isdl

    @downloadActive.setter
    def downloadActive(self, value):
        self.mutex.lock()
        self._downloadActive = value
        self.mutex.unlock()
        self.downloadActiveUpdate.emit()

    def __init__(self, loglevel='WARNING', netWorker = None, mqtt = None, url = '', cacheFile = None):
        QObject.__init__(self)

        self.logger = Logger(name='ratt.acl')
        self.logger.setLogLevelStr('INFO')
        self.debug = self.logger.isDebug()

        if netWorker is None:
            self.logger.error('must set netWorker')
            exit(-1)

        self.netWorker = netWorker

        self.url = url

        self.cacheFile = cacheFile

        self.mutex = QMutex()

        self._acl = json.loads('[]')
        self._hash = ''
        self._numRecords = 0
        self._numActiveRecords = 0

        self._downloadActive = False
        self._date = int(time.time())
        self._status = 'initialized'

        self.loadFile(self.cacheFile)

        self.mqtt = mqtt
        self.mqtt.broadcastEvent.connect(self.__slotBroadcastMQTTEvent)
        self.mqtt.targetedEvent.connect(self.__slotTargetedMQTTEvent)

    def loadFile(self, filename=None):
        self.logger.info('loading ACL file %s' % filename)
        if filename is not None:
            f = QFile(filename)

            if not f.open(QIODevice.ReadOnly | QIODevice.Text):
                self.logger.error('error opening ACL file %s for read' % filename)
                return False

            bytes = f.readAll()

            if bytes.isEmpty():
                self.logger.error('unabled to read from ACL file %s' % filename)
                f.close()
                return False

            f.close()

            info = QFileInfo(filename)
            modified = int(info.lastModified().toMSecsSinceEpoch() / 1000)

            return self.parseJSON(doc=str(bytes), save=False, date=modified, status='loaded_from_file')

        return False

    def saveFile(self, filename=None):
        self.logger.info('saving ACL cache file %s' % filename)
        if filename is not None:

            self.mutex.lock()
            doc = json.dumps(self._acl)
            self.mutex.unlock()

            f = QFile(filename)

            if not f.open(QIODevice.WriteOnly):
                self.logger.error('error opening ACL cache file %s for write' % filename)
                return False

            if f.write(str(doc)) == -1:
                f.close()
                self.logger.error('unabled to write to ACL cache file %s' % filename)
                return False

            f.close()
            return True

        return False

    @pyqtSlot()
    def download(self):
        if not self.downloadActive:
            self.logger.info('downloading ACL from ' + self.url)
            self.reply = self.netWorker.get(url=QUrl(self.url))
            self.reply.finished.connect(self.slotDownloadFinished)
            self.downloadActive = True
            return True
        else:
            self.logger.warning('already busy downloading ACL')
        return False


    def slotDownloadFinished(self):
        self.logger.info('ACL download finished')

        error = self.reply.error()

        if error == QNetworkReply.NoError:
            self.logger.debug('no error, parsing response')
            self.parseJSON(doc=str(self.reply.readAll()), save=True, status='downloaded')

        else:
            self.logger.error('NetWorker response error: %s (%s)' % (error, self.reply.errorString()))

        self.reply.deleteLater()
        self.downloadActive = False


    def search(self, hash):
        self.mutex.lock()
        found_record = []

        for record in self._acl:
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

    def calcHash(self, j):
        m = hashlib.sha224()
        m.update(str(j).encode())
        hash = m.hexdigest()
        return hash

    def parseJSON(self, doc, save=False, date=None, status=''):
        try:
            parsed = json.loads(doc)
            count = len(parsed)
            active = self.countActive(parsed)
            hash = self.calcHash(parsed)

            self.logger.debug('parseJSON hash=%s stored hash=%s' % (hash, self._hash))
            if hash != self._hash:
                self.mutex.lock()
                self._acl = parsed
                self._numRecords = count
                self._numActiveRecords = active
                self._hash = hash
                if date is None:
                    self._date = int(time.time())
                else:
                    self._date = date
                self._status = status
                self.mutex.unlock()

                self.logger.info('updated ACL with %d entries, %d active, hash=%s' % (self._numRecords, self._numActiveRecords, self._hash))
                self.update.emit()

                if save:
                    self.saveFile(self.cacheFile)

                return True

            else:
                self.mutex.lock()
                if date is None:
                    self._date = int(time.time())
                self._status = 'same_hash'
                self.mutex.unlock()
                self.update.emit()
                self.logger.error('no ACL update because same hash=%s' % (self._hash))

        except:
            self.logger.exception('json parse error')
            self.updateError.emit()

        return False


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
