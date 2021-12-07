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
# copy of this software and assoceiated documentation files (the "Software"),
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

from PyQt5.QtCore import QObject, QMutex, QIODevice, pyqtSlot, pyqtSignal, pyqtProperty, QVariant, QUrl
from PyQt5.QtCore import QFile, QFileInfo
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from Logger import Logger
import json
import hashlib
import time

class CachedRemoteFile(QObject):
    update = pyqtSignal()
    updateError = pyqtSignal(name='updateError')
    updateErrorDesc = pyqtSignal()
    downloadActiveUpdate = pyqtSignal()

    @pyqtProperty(str, notify=update)
    def hash(self):
        self.mutex.lock()
        h = self._hash
        self.mutex.unlock()
        return h

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

    @pyqtProperty(str, notify=updateErrorDesc)
    def errorDescription(self):
        self.mutex.lock()
        s = self._error
        self.mutex.unlock()
        return s


    @pyqtProperty(str, notify=update)
    def source(self):
        self.mutex.lock()
        s = self._source
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

    def __init__(self):
        QObject.__init__(self)

        self.mutex = QMutex()

        self._downloadActive = False
        self._date = int(time.time())
        self._status = 'initialized'
        self._error = ''
        self._source = ''
        self._doc = None
        self._obj = json.loads('[]')
        self._hash = ''

    def setup(self, logger=None, netWorker=None, url=None, cacheFile=None):
        assert logger
        assert netWorker
        assert url
        assert cacheFile

        self.logger = logger
        self.netWorker = netWorker
        self.url = url

        self.cacheFile = cacheFile

        self.loadFile(self.cacheFile)

    def getDoc(self):
        self.mutex.lock()
        doc = self._doc
        self.mutex.unlock()
        return doc

    def getObj(self):
        self.mutex.lock()
        obj = self._obj
        self.mutex.unlock()
        return obj


    @pyqtSlot()
    def download(self):
        if not self.downloadActive:
            self.downloadActive = True

            self.logger.info('downloading from ' + self.url)
            self.reply = self.netWorker.get(url=QUrl(self.url))
            self.reply.finished.connect(self.slotDownloadFinished)

            self.logger.debug('self.reply.error=' + str(self.reply.error()))

            if self.reply.error() != QNetworkReply.NoError:
                self.downloadError(self.reply.error())
                self.reply.deleteLater()
                return False

            self._error = ''
            self.updateErrorDesc.emit()
            return True
        else:
            self.logger.warning('already busy downloading ' + self.url)
        return False

    def downloadError(self, error, errorString):
        self.logger.error('DOWNLOAD ERROR: %s (%s) %s' % (error, errorString, self.url))
        self.updateError.emit()

        self._error = errorString
        self.updateErrorDesc.emit()

        self.downloadActive = False

    @pyqtSlot()
    def slotDownloadFinished(self):
        self.logger.info('remote download finished from ' + self.url)
        error = self.reply.error()

        if error == QNetworkReply.NoError:
            self.logger.debug('parsing download response')
            self._source = self.url
            self.parseJSON(doc=str(self.reply.readAll(), encoding='utf-8'), save=True, status='downloaded')
        else:
            self.downloadError(self.reply.error(), self.reply.errorString())

        self.reply.deleteLater()
        self.downloadActive = False

    def saveFile(self, filename=None):
        self.logger.info('saving cache file %s' % filename)
        if filename is not None:
            self.mutex.lock()
            doc = self._doc
            self.mutex.unlock()

            f = QFile(filename)

            if not f.open(QIODevice.WriteOnly):
                self.logger.error('error opening cache file %s for write' % filename)
                return False

            if f.write(doc.encode()) == -1:
                f.close()
                self.logger.error('unabled to write to cache file %s' % filename)
                return False

            f.close()
            return True

        return False

    def loadFile(self, filename=None):
        self.logger.info('loading cache file %s' % filename)
        if filename is not None:
            f = QFile(filename)

            if not f.open(QIODevice.ReadOnly | QIODevice.Text):
                self.logger.error('error opening cache file %s for read' % filename)
                return False

            bytes = f.readAll()

            if bytes.isEmpty():
                self.logger.error('unabled to read from cache file %s' % filename)
                f.close()
                return False

            f.close()

            info = QFileInfo(filename)
            modified = int(info.lastModified().toMSecsSinceEpoch() / 1000)

            self._source = 'file://' + filename
            return self.parseJSON(doc=str(bytes, encoding='utf-8'), save=False, date=modified, status='loaded')

        return False

    def calcHash(self, j):
        m = hashlib.sha224()
        m.update(str(j).encode())
        hash = m.hexdigest()
        return hash

    # this hook is called just after parsing but before hashes are checked
    # the mutex is not held at this point
    def parseJSON__hook_unlocked(self, parsed):
        return None

    # this hook is called if the hashes differ, and the mutex IS held
    def parseJSON__hook_locked(self, o):
        pass

    def parseJSON(self, doc, save=False, date=None, status=''):
        try:
            parsed = json.loads(doc)
            hash = self.calcHash(doc)
            o = self.parseJSON__hook_unlocked(parsed)

            self.logger.debug('parseJSON hash=%s stored hash=%s' % (hash, self._hash))
            if hash != self._hash:
                self.mutex.lock()
                self._doc = doc
                self._obj = parsed
                self._hash = hash
                if date is None:
                    self._date = int(time.time())
                else:
                    self._date = date
                self._status = status

                if o is not None:
                    self.parseJSON__hook_locked(o)

                self.mutex.unlock()

                self.logger.info('updated remote config hash=%s' % (self._hash))
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

                self.logger.info('no update because same hash=%s' % (self._hash))
                self.update.emit()

        except:
            self.logger.exception('json parse error')
            self._status = 'json_error'
            self.updateError.emit()

        return False
