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

from PyQt5.QtCore import Qt, QObject, QUrl, QFile, QIODevice, QByteArray, QDateTime, QMutex, pyqtSignal, pyqtProperty
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from Logger import Logger
import logging
import simplejson as json
import hashlib

class ACL(QObject):
    updateError = pyqtSignal(name='updateError')
    update = pyqtSignal()

    @pyqtProperty(str, notify=update)
    def hash(self):
        return self._hash

    @pyqtProperty(int, notify=update)
    def numRecords(self):
        return self._numRecords

    @pyqtProperty(int, notify=update)
    def numActiveRecords(self):
        return self._numActiveRecords

    def __init__(self, loglevel='WARNING', netWorker = None, url=''):
        QObject.__init__(self)

        self.logger = Logger(name='ratt.acl')
        self.logger.setLogLevelStr(loglevel)
        self.debug = self.logger.isDebug()

        if netWorker is None:
            self.logger.error('must set netWorker')
            exit(-1)

        self.netWorker = netWorker

        self.url = url

        self.mutex = QMutex()

        self._acl = json.loads('[]')
        self._hash = ''
        self._numRecords = 0
        self._numActiveRecords = 0

    def download(self):
        self.logger.info('downloading ACL from ' + self.url)

        self.reply = self.netWorker.get(url=QUrl(self.url))

        self.reply.finished.connect(self.slotDownloadFinished)


    def slotDownloadFinished(self):
        self.logger.info('ACL download finished')
        error = self.reply.error()

        if error == QNetworkReply.NoError:
            self.logger.debug('no error, parsing response')
            self.parseJSON(doc=str(self.reply.readAll()))

        else:
            self.logger.error('NetWorker response error: %s (%s)' % (error, self.reply.errorString()))

        self.reply.deleteLater()


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

    def parseJSON(self, doc):
        try:
            parsed = json.loads(doc)
            count = len(parsed)
            active = self.countActive(parsed)
            hash = self.calcHash(parsed)

            self.mutex.lock()
            self._acl = parsed
            self._numRecords = count
            self._numActiveRecords = active
            self._hash = hash
            self.mutex.unlock()

            self.logger.info('parsed ACL with %d entries, %d active, hash=%s' % (self._numRecords, self._numActiveRecords, self._hash))

            self.update.emit()
        except:
            self.logger.warning('json parse error')
            self.updateError.emit()
