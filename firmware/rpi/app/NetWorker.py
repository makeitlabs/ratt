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

from PyQt5.QtCore import Qt, QObject, QUrl, QFile, QIODevice, QByteArray, QDateTime, QMutex, pyqtSignal
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QSsl, QSslConfiguration, QSslKey, QSslCertificate, QSslSocket
from Logger import Logger
import logging
import simplejson as json
import hashlib

class NetWorker(QObject):
    def __init__(self, loglevel='WARNING'):
        QObject.__init__(self)

        self.logger = Logger(name='ratt.networker')
        self.logger.setLogLevelStr(loglevel)
        self.debug = self.logger.isDebug()

        self.mgr = QNetworkAccessManager()
        self.sslConfig = QSslConfiguration()
        self.sslSupported = QSslSocket.supportsSsl()

        self.setAuth()
        self.setSSLCertConfig()

        self.mgr.authenticationRequired.connect(self.handleAuthenticationRequired)


    #def log(self):
    #    self.logger.debug('posting log to ' + self.LogUrl)
    #    self.post(url=self.LogUrl)


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

