from PyQt5.QtCore import Qt, QObject, QUrl, QFile, QIODevice, QByteArray, QDateTime
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QSsl, QSslConfiguration, QSslKey, QSslCertificate, QSslSocket
import json

class NetWorker(QObject):
    def __init__(self):
        QObject.__init__(self)

        self.mgr = QNetworkAccessManager()
        self.sslConfig = QSslConfiguration()
        self.ssl = QSslSocket.supportsSsl()

        self.setAuth()
        self.setCertFiles()
        
        if self.ssl:
            self.configureCerts()

    def setAuth(self, user = '', password = ''):
        self.user = user
        self.password = password

    def setCertFiles(self, caCertFile = '/home/pi/ssl/cacert.pem', clientCertFile = '/home/pi/ssl/client_cert.pem', clientKeyFile = '/home/pi/ssl/client_key.pem'):
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
            doc = str(reply.readAll(), 'utf-8')
            j = json.loads(doc)
            print (json.dumps(j, sort_keys=True, indent=1))
            
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
            print('WARNING: private key is null')
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
        
        

