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
# --------------------------------------------------------------------------
#
# Author: Steve Richardson (steve.richardson@makeitlabs.com)
#

from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5 import QtCore
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from NetWorker import NetWorker
from RFID import RFID
import ConfigParser

class RattAppEngine(QQmlApplicationEngine):
    def __init__(self):
        QQmlApplicationEngine.__init__(self)

        self.netWorker = NetWorker()
        #self.netWorker.setAuth(user='api', password='s33krit')

        self.rfid = RFID("/dev/ttyAMA0")

        self.rootContext().setContextProperty("appEngine", self)
        self.rootContext().setContextProperty("netWorker", self.netWorker)
        self.rootContext().setContextProperty("rfid", self.rfid)

        self.rfid.monitor()

    @Slot()
    def testUpdateACL(self):
        print('testing acl download')
        #self.netWorker.get(url='https://192.168.0.24:8443/auth/api/v1/resources/frontdoor/acl')
        self.netWorker.get(url='http://jsonplaceholder.typicode.com/posts/1')

    @Slot()
    def testPostLog(self):
        print('testing log post')
        #self.netWorker.post(url='https://192.168.0.24:8443/auth/api/v1/resources/frontdoor/log')
        self.netWorker.post(url='http://jsonplaceholder.typicode.com/posts')
