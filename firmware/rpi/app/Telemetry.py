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

class Telemetry(QObject):

    def __init__(self, loglevel='WARNING', netWorker = None, url='', cacheFile=None):
        QObject.__init__(self)

        self.logger = Logger(name='ratt.telemetry')
        self.logger.setLogLevelStr(loglevel)
        self.debug = self.logger.isDebug()

        if netWorker is None:
            self.logger.error('must set netWorker')
            exit(-1)

        self.netWorker = netWorker

        self.url = url

        self.cacheFile = cacheFile

        self.mutex = QMutex()

    def logEvent(self, event_type, message):
        self.logger.info('logging event to ' + self.url)

        qvars = {}

        now = QDateTime.currentDateTime()
        unix_time = now.toMSecsSinceEpoch()
        qvars['event_date'] = str(unix_time / 1000)

        qvars['event_type'] = event_type
        qvars['message'] = message

        q = self.netWorker.buildQuery(qvars)
        r = self.netWorker.buildRequest(url=QUrl(self.url))

        self.reply = self.netWorker.post(request=r, query=q)

        self.reply.finished.connect(self.slotLogEventFinished)


    def slotLogEventFinished(self):
        self.logger.info('log event finished')
        error = self.reply.error()

        if error == QNetworkReply.NoError:
            self.logger.debug('no error, response: %s' % reply.readAll())

        else:
            self.logger.error('NetWorker response error: %s (%s)' % (error, self.reply.errorString()))

        self.reply.deleteLater()
