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

from PyQt5.QtCore import Qt, QObject, QUrl, QFile, QIODevice, QByteArray, QDateTime, QMutex, QTimer, pyqtSignal, pyqtProperty
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QSsl, QSslConfiguration, QSslKey, QSslCertificate, QSslSocket
from PyQt5.QtNetwork import QNetworkInterface, QNetworkAddressEntry, QHostAddress, QAbstractSocket
from Logger import Logger
import logging
import simplejson as json
import hashlib
from commands import getoutput

class NetWorker(QObject):
    ifcAddrChanged = pyqtSignal(str, name='ifcAddrChanged', arguments=['ip'])
    currentIfcAddrChanged = pyqtSignal()
    wifiStatus = pyqtSignal(str, str, int, int, name='wifiStatus', arguments=['essid', 'freq', 'quality', 'level'])
    wifiStatusChanged = pyqtSignal()

    @pyqtProperty(str, notify=currentIfcAddrChanged)
    def currentIfcAddr(self):
        return self.ifcAddr.toString()

    @pyqtProperty(str)
    def currentHwAddr(self):
        return self.hwAddr

    @pyqtProperty(str, notify=wifiStatusChanged)
    def currentWifiESSID(self):
        return self.essid

    @pyqtProperty(str, notify=wifiStatusChanged)
    def currentWifiFreq(self):
        return self.freq

    @pyqtProperty(int, notify=wifiStatusChanged)
    def currentWifiQuality(self):
        return self.quality

    @pyqtProperty(int, notify=wifiStatusChanged)
    def currentWifiLevel(self):
        return self.level

    def __init__(self, loglevel='WARNING', ifcName='wlan0', mqtt=None):
        QObject.__init__(self)

        self.logger = Logger(name='ratt.networker')
        self.logger.setLogLevelStr(loglevel)
        self.debug = self.logger.isDebug()

        self._mqtt = mqtt

        self.mgr = QNetworkAccessManager()
        self.sslConfig = QSslConfiguration()
        self.sslSupported = QSslSocket.supportsSsl()

        self.setAuth()
        self.setSSLCertConfig()

        self.mgr.authenticationRequired.connect(self.handleAuthenticationRequired)

        self.ifcName = ifcName
        self.ifcAddr = QHostAddress()
        self.hwAddr = self.getHwAddress(ifc=ifcName)

        self.statusTimer = QTimer()
        self.statusTimer.setSingleShot(False)
        self.statusTimer.timeout.connect(self.slotStatusTimer)
        self.statusTimer.start(15000)

        self.essid = ''
        self.freq = ''
        self.quality = 0
        self.level = 0

        self.ifcAddrChanged.connect(self.slotIfcAddrChanged)
        self.wifiStatus.connect(self.slotWifiStatus)


    def slotStatusTimer(self):
        ip = self.getIfcAddress(ifc=self.ifcName)

        if ip != self.ifcAddr:
            self.ifcAddr = ip
            self.ifcAddrChanged.emit(ip.toString())
            self.currentIfcAddrChanged.emit()

        results = { }
        if self.getWifiStatus(results):
            self.essid = results['essid']
            self.freq = results['freq']
            self.quality = results['quality']
            self.level = results['level']
            self.wifiStatus.emit(self.essid, self.freq, self.quality, self.level)
            self.wifiStatusChanged.emit()


    # ['wlan0', 'IEEE', '802.11', 'ESSID:"FooBar"', 'Mode:Managed', 'Frequency:2.412',
    # 'GHz', 'Access', 'Point:', '00:11:22:33:44:55', 'Bit', 'Rate=65', 'Mb/s', 'Tx-Power=31',
    # 'dBm', 'Retry', 'short', 'limit:7', 'RTS', 'thr:off', 'Fragment', 'thr:off', 'Power',
    # 'Management:on', 'Link', 'Quality=43/70', 'Signal', 'level=-67', 'dBm', 'Rx', 'invalid',
    # 'nwid:0', 'Rx', 'invalid', 'crypt:0', 'Rx', 'invalid', 'frag:0', 'Tx', 'excessive', 'retries:113',
    # 'Invalid', 'misc:0', 'Missed', 'beacon:0']
    def getWifiStatus(self, res):
        try:
            iw = getoutput('/sbin/iwconfig %s' % self.ifcName)

            fields = iw.split()

            for field in fields:
                if field.find('ESSID') != -1:
                    res['essid'] = field.split('"')[1]
                elif field.find('Frequency') != -1:
                    res['freq'] = field.split(':')[1]
                elif field.find('Quality') != -1:
                    frac = field.split('=')[1]
                    (n, d) = frac.split('/')
                    q = int(n)*100 / int(d)
                    res['quality'] = q
                elif field.find('level') != -1:
                    res['level'] = int(field.split('=')[1])
        except:
            return False

        return True


    def getIfcAddress(self, ifc):
        myIfc = QNetworkInterface.interfaceFromName(ifc)
        addrList = myIfc.addressEntries()

        for addr in addrList:
            if addr.ip().protocol() == QAbstractSocket.IPv4Protocol:
                return addr.ip()

        return QHostAddress()

    def getHwAddress(self, ifc):
        myIfc = QNetworkInterface.interfaceFromName(ifc)

        return myIfc.hardwareAddress()


    def setAuth(self, user = '', password = ''):
        self.user = user
        self.password = password

    def setSSLCertConfig(self, enabled = False, caCertFile = '', clientCertFile = '', clientKeyFile = ''):
        self.sslEnabled = enabled

        if self.sslSupported and self.sslEnabled:
            self.caCertFile = caCertFile
            self.clientCertFile = clientCertFile
            self.clientKeyFile = clientKeyFile

            self.configureCerts()

    def get(self, url):
        self.logger.debug('get url=%s' % url.toString())

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader("User-Agent", "RATT")

        if self.sslSupported and self.sslEnabled:
            request.setSslConfiguration(self.sslConfig)

        reply = self.mgr.get(request)

        if self.sslSupported and self.sslEnabled:
            reply.sslErrors.connect(self.handleSSLErrors)

        return reply

    def buildRequest(self, url):
        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")

        return request

    def buildQuery(self, vars):
        query = str()
        for key in vars:
            value = vars[key]
            sep = '&' if query != '' else ''
            query = query + '%s%s=%s' % (sep, key, value)

        return query

    def post(self, request, query):
        self.logger.debug('post url=%s query=%s' % (request.url().toString(), query))

        if self.sslSupported and self.sslEnabled:
            request.setSslConfiguration(self.sslConfig)

        bytearray = QByteArray()
        bytearray.append(query)

        reply = self.mgr.post(request, bytearray)

        if self.sslSupported and self.sslEnabled:
            self.mgr.sslErrors.connect(self.handleSSLErrors)

        return reply

    def handleSSLErrors(self, reply, errors):
        for err in errors:
            self.logger.error('SSL errors:' + err.errorString())

    def handleAuthenticationRequired(self, reply, authenticator):
        if self.user == '' and self.password == '':
            self.logger.warning('authentication required and no user/password set')

        authenticator.setUser(self.user)
        authenticator.setPassword(self.password)

    def configureCerts(self):
        ## import the private client key
        privateKeyFile = QFile(self.clientKeyFile)
        privateKeyFile.open(QIODevice.ReadOnly)
        privateKey = QSslKey(privateKeyFile, QSsl.Rsa)

        if privateKey.isNull():
            self.logger.warning('SSL private key is null')
        else:
            self.sslConfig.setPrivateKey(privateKey)

        ## import the client certificate
        certFile = QFile(self.clientCertFile)
        certFile.open(QIODevice.ReadOnly)
        cert = QSslCertificate(certFile)
        self.sslConfig.setLocalCertificate(cert)

        ## import the self-signed CA certificate
        caCertFile = QFile(self.caCertFile)
        caCertFile.open(QIODevice.ReadOnly)
        caCert = QSslCertificate(caCertFile)

        ## add self-signed CA cert to the other CA certs
        caCertList = self.sslConfig.caCertificates()
        caCertList.append(caCert)
        self.sslConfig.setCaCertificates(caCertList)

    def slotWifiStatus(self, essid, freq, quality, level):
        self.logger.debug("WIFI STATUS %s %sGHz quality=%d%% level=%ddBm" % (essid, freq, quality, level))
        self._mqtt.publish(subtopic='wifi/essid', msg=essid)
        self._mqtt.publish(subtopic='wifi/freq', msg=freq)
        self._mqtt.publish(subtopic='wifi/quality', msg=quality)
        self._mqtt.publish(subtopic='wifi/level', msg=level)

    def slotIfcAddrChanged(self, ipStr):
        self.logger.debug("IP CHANGED %s" % ipStr)
