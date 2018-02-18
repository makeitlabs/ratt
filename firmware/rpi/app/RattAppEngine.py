# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5 import QtCore
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterType
from NetWorker import NetWorker
from RFID import RFID

class RattAppEngine(QQmlApplicationEngine):
    def __init__(self):
        QQmlApplicationEngine.__init__(self)

        self.netWorker = NetWorker()
        #self.netWorker.setAuth(user='api', password='s33krit')

        self.rfid = RFID("/dev/ttyAMA0")

        self.rootContext().setContextProperty("appEngine", self)
        self.rootContext().setContextProperty("netWorker", self.netWorker)
        self.rootContext().setContextProperty("rfid", self.rfid)

        self.rfid.transaction()

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
