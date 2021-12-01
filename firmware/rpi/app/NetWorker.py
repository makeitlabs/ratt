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
import json
import hashlib
import subprocess
import re

class NetWorker(QObject):
    ifcAddrChanged = pyqtSignal(str, name='ifcAddrChanged', arguments=['ip'])
    currentIfcAddrChanged = pyqtSignal()
    currentIfcHwAddrChanged = pyqtSignal()
    wifiStatus = pyqtSignal(str, str, str, int, int, str, str, name='wifiStatus', arguments=['essid', 'ap', 'freq', 'quality', 'level', 'rxrate', 'txrate'])
    wifiStatusChanged = pyqtSignal()

    @pyqtProperty(str, notify=currentIfcAddrChanged)
    def currentIfcAddr(self):
        return self.ifcAddr.toString()

    @pyqtProperty(str, notify=currentIfcHwAddrChanged)
    def currentHwAddr(self):
        return self.hwAddr

    @pyqtProperty(str, notify=wifiStatusChanged)
    def currentWifiESSID(self):
        return self.essid

    @pyqtProperty(str, notify=wifiStatusChanged)
    def currentWifiAP(self):
        return self.ap

    @pyqtProperty(str, notify=wifiStatusChanged)
    def currentWifiFreq(self):
        return self.freq

    @pyqtProperty(int, notify=wifiStatusChanged)
    def currentWifiQuality(self):
        return self.quality

    @pyqtProperty(int, notify=wifiStatusChanged)
    def currentWifiLevel(self):
        return self.level

    @pyqtProperty(int, notify=wifiStatusChanged)
    def currentTxRate(self):
        return self.txrate

    @pyqtProperty(int, notify=wifiStatusChanged)
    def currentRxRate(self):
        return self.rxrate

    def __init__(self, loglevel='WARNING', ifcName='wlan0', ifcMacAddressOverride=None, mqtt=None):
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
        self.authAttempts = 0

        self.ifcName = ifcName
        self.ifcAddr = QHostAddress()

        if ifcMacAddressOverride is not None:
            self.hwAddr = ifcMacAddressOverride
        else:
            self.hwAddr = self.getHwAddress(ifc=ifcName)

        self.statusTimer = QTimer()
        self.statusTimer.setSingleShot(False)
        self.statusTimer.timeout.connect(self.slotStatusTimer)
        self.statusTimer.start(15000)

        self.essid = ''
        self.ap = ''
        self.freq = ''
        self.quality = 0
        self.level = 0
        self.rxrate = ''
        self.txrate = ''

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
            self.ap = results['ap']
            self.freq = results['freq']
            self.quality = results['quality']
            self.level = results['level']
            self.rxrate = results['rxrate']
            self.txrate = results['txrate']
            self.wifiStatus.emit(self.essid, self.ap, self.freq, self.quality, self.level, self.rxrate, self.txrate)
            self.wifiStatusChanged.emit()
            self._mqtt.publish(subtopic='wifi/status', msg=json.dumps(results))

    def getWifiStatus(self, res):
        try:
            # note, scraping iw output is not recommended but we do what we must.
            iw = str(subprocess.check_output(['/usr/sbin/iw', self.ifcName, 'link']))

            if ('Usage:' in iw):
                res['quality'] = 75
                res['level'] = -57
                res['freq'] = '2447'
                res['ap'] = '00:01:02:03:04:05'
                res['essid'] = 'Simulator'
                res['txrate'] = '1.0 MBit/s'
                res['rxrate'] = '1.0 MBit/s'
                return True


            level = int(re.search('signal: .*? dBm', iw).group(0).split(': ')[1].split(' ')[0])
            res['level'] = level

            q = 110 + level
            if (q < 0):
                q = 0
            elif (q > 100):
                q = 100

            res['quality'] = q
            res['freq'] = re.search('freq: [0-9]{1,10}', iw).group(0).split(': ')[1]
            res['ap'] = re.search('Connected to ([0-9A-Fa-f]{2}[:]{0,1}){6}', iw).group(0).split(' ')[2]
            res['essid'] = re.search('SSID: .*', iw).group(0).split('\\n')[0].split(': ')[1]

            iw = str(subprocess.check_output(['/usr/sbin/iw', self.ifcName, 'station', 'dump']))

            res['txrate'] = re.search('tx bitrate:.*', iw).group(0).split('\\t')[1].split('\\n')[0]
            res['rxrate'] = re.search('rx bitrate:.*', iw).group(0).split('\\t')[1].split('\\n')[0]

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
        self.logger.debug('HTTP GET URL %s' % url.toString())

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(("User-Agent").encode("utf-8"), ("RATT").encode("utf-8"))

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

    def handleSSLErrors(self, errors):
        for err in errors:
            self.logger.error('SSL errors:' + err.errorString())

    def handleAuthenticationRequired(self, reply, authenticator):
        self.logger.debug("AUTH REQUIRED")
        self.authAttempts = self.authAttempts + 1

        if self.authAttempts > 2:
            self.logger.error('authentication failure, check the user/password in the config')

        elif self.user == '' and self.password == '':
            self.logger.error('authentication required and no user/password set')

        else:
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

    def slotWifiStatus(self, essid, ap, freq, quality, level, rxrate, txrate):
        self.logger.debug("WIFI STATUS %s %s %s quality=%d%% level=%ddBm rxrate=%s txrate=%s" % (essid, ap, freq, quality, level, rxrate, txrate))

    def slotIfcAddrChanged(self, ipStr):
        self.logger.debug("IP CHANGED %s" % ipStr)
