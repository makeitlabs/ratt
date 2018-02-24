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
import simplejson as json
import hashlib

class NetWorker(QObject):
    aclUpdate = pyqtSignal(int, int, str, name='aclUpdate', arguments=['total', 'active', 'hash'])
    aclUpdateError = pyqtSignal(name='aclUpdateError')

    def __init__(self):
        QObject.__init__(self)

        self.mutex = QMutex()
        self.acl = json.loads('[]')

        self.mgr = QNetworkAccessManager()
        self.sslConfig = QSslConfiguration()
        self.ssl = QSslSocket.supportsSsl()

        self.setAuth()
        self.setCertFiles()
        
        if self.ssl:
            self.configureCerts()

    def searchAcl(self, hash):
        self.mutex.lock()
        found_record = []

        for record in self.acl:
            if record['tagid'] == hash:
                found_record = record
                break

        self.mutex.unlock()
        return found_record

    def countAclActive(self):
        self.mutex.lock()
        active = 0

        for record in self.acl:
            if record['allowed'] == 'allowed':
                active = active + 1

        self.mutex.unlock()
        return active

    def hashAcl(self):
        self.mutex.lock()

        m = hashlib.sha224()
        m.update(str(self.acl).encode())
        hash = m.hexdigest()

        self.mutex.unlock()
        return hash

    def setAuth(self, user = '', password = ''):
        self.user = user
        self.password = password

    def setCertFiles(self, caCertFile = '/etc/ssl/cacert.pem', clientCertFile = '/etc/ssl/client_cert.pem', clientKeyFile = '/etc/ssl/client_key.pem'):
        self.caCertFile = caCertFile
        self.clientCertFile = clientCertFile
        self.clientKeyFile = clientKeyFile

    def post(self, url):
        # there must be a nicer way to build the request
        req = QNetworkRequest(QUrl(url))
        req.setHeader(QNetworkRequest.ContentTypeHeader, "application/x-www-form-urlencoded")

        now = QDateTime.currentDateTime()
        unix_time = now.toMSecsSinceEpoch()
        p = 'event_date=' + str(unix_time)

        p = p + '&event_type=test&member=Ralph.Teste&message=RATT'

        ba = QByteArray()
        ba.append(p)
        
        self.mgr.finished.connect(self.handlePostResponse)
        self.mgr.authenticationRequired.connect(self.handleAuthenticationRequired)

        if self.ssl:
            self.mgr.sslErrors.connect(self.handleSSLErrors)
            req.setSslConfiguration(self.sslConfig)

        self.mgr.post(req, ba)
        
    def get(self, url):
        print('get url=%s' % (url))
        req = QNetworkRequest(QUrl(url))

        self.mgr.finished.connect(self.handleGetResponse)
        self.mgr.authenticationRequired.connect(self.handleAuthenticationRequired)

        if self.ssl:
            self.mgr.sslErrors.connect(self.handleSSLErrors)
            req.setSslConfiguration(self.sslConfig)

        self.mgr.get(req)
            
        
    def handleSSLErrors(self, reply, errors):
        for err in errors:
            print('SSL errors:' + err.errorString())
        
    def handleAuthenticationRequired(self, reply, authenticator):
        if self.user == '' and self.password == '':
            print('WARNING: authentication required and no user/password set')

        authenticator.setUser(self.user)
        authenticator.setPassword(self.password)


    def handlePostResponse(self, reply):
        print('handlePostResponse')
        error = reply.error()

        if error == QNetworkReply.NoError:
            print (reply.readAll())
            
        else:
            print('NetWorker response error: ', error)
            print(reply.errorString())

        self.mgr.finished.disconnect(self.handlePostResponse)
        self.mgr.authenticationRequired.disconnect(self.handleAuthenticationRequired)
        if self.ssl:
            self.mgr.sslErrors.disconnect(self.handleSSLErrors)


    def handleGetResponse(self, reply):
        print('handleGetResponse')
        error = reply.error()

        if error == QNetworkReply.NoError:
            doc = str(reply.readAll())

            try:
                j = json.loads(doc)

                self.mutex.lock()
                self.acl = j
                total = len (self.acl)
                self.mutex.unlock()

                active = self.countAclActive()
                hash = self.hashAcl()

                print('json acl with %d entries, %d active, hash=%s' % (total, active, hash))

                self.aclUpdate.emit(total, active, hash)
            except:
                print('json parse error')
                self.aclUpdateError.emit()

            
        else:
            print('NetWorker response error: ', error)
            print(reply.errorString())

        self.mgr.finished.disconnect(self.handleGetResponse)
        self.mgr.authenticationRequired.disconnect(self.handleAuthenticationRequired)
        if self.ssl:
            self.mgr.sslErrors.disconnect(self.handleSSLErrors)
            
    def configureCerts(self):
        ## import the private client key
        privateKeyFile = QFile(self.clientKeyFile)
        privateKeyFile.open(QIODevice.ReadOnly)
        privateKey = QSslKey(privateKeyFile, QSsl.Rsa)

        if privateKey.isNull():
            print('  WARNING: private key is null')
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
        
        

