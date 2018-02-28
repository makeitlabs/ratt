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

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QVariant
from PyQt5 import QtCore
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from RattConfig import RattConfig
from NetWorker import NetWorker
from RFID import RFID
from MemberRecord import MemberRecord

class RattAppEngine(QQmlApplicationEngine):
    validScan = pyqtSignal(MemberRecord, name='validScan', arguments=['record'])
    invalidScan = pyqtSignal(str, name='invalidScan', arguments=['reason'])

    def __init__(self):
        QQmlApplicationEngine.__init__(self)

        self.config = RattConfig()

        self.netWorker = NetWorker()
        self.netWorker.setSSLCertConfig(enabled=self.config.value('SSL.Enabled'),
                                        caCertFile=self.config.value('SSL.CaCertFile'),
                                        clientCertFile=self.config.value('SSL.ClientCertFile'),
                                        clientKeyFile=self.config.value('SSL.ClientKeyFile'))

        self.netWorker.setAuth(user=self.config.value('Auth.HttpAuthUser'),
                               password=self.config.value('Auth.HttpAuthPassword'))

        self.netWorker.setUrls(acl=self.config.value('Auth.AclUrl'),
                               log=self.config.value('Auth.LogUrl'))

        self.rfid = RFID(self.config.value('RFID.SerialPort'))

        self.activeMemberRecord = MemberRecord()

        self.rootContext().setContextProperty("appEngine", self)
        self.rootContext().setContextProperty("config", self.config)
        self.rootContext().setContextProperty("netWorker", self.netWorker)
        self.rootContext().setContextProperty("rfid", self.rfid)
        self.rootContext().setContextProperty("activeMemberRecord", self.activeMemberRecord)

        qmlRegisterType(MemberRecord, 'RATT', 1, 0, 'MemberRecord')

        self.rfid.tagScan.connect(self.tagScanHandler)

        self.rfid.monitor()

        self.netWorker.fetchAcl()



    def tagScanHandler(self, tag, hash, time, debugText):
        print('tag scanned tag=%d hash=%s time=%d debug=%s' % (tag, hash, time, debugText))

        result = self.netWorker.searchAcl(hash)

        if result != []:
            success = self.activeMemberRecord.parseRecord(result)

            if success:
                self.validScan.emit(self.activeMemberRecord)
            else:
                self.invalidScan.emit('could not create MemberRecord')
                print('error making member record')
        else:
            self.activeMemberRecord.clearRecord()
            self.invalidScan.emit('unknown rfid tag')
            print('unknown rfid tag')

