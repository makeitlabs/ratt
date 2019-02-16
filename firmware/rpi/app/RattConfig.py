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
from PyQt5.QtQml import QQmlListProperty, qmlRegisterType
import ConfigParser
from Logger import Logger
import simplejson as json
from CachedRemoteFile import CachedRemoteFile

class Issue(QObject):
    nameChanged = pyqtSignal()

    def __init__(self, name='', *args, **kwargs):
        super(Issue, self).__init__(*args, **kwargs)
        self._name = name

    @pyqtProperty('QString', notify=nameChanged)
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name != self._name:
            self._name = name
            self.nameChanged.emit()

class RattConfig(QObject):
    configChanged = pyqtSignal()

    @pyqtProperty(bool, notify=configChanged)
    def haveInitialRemoteConfig(self):
        return self._haveInitialRemoteConfig

    def __init__(self, inifile, loglevel='INFO'):
        QObject.__init__(self)

        self.logger = Logger(name='ratt.config')
        self.logger.setLogLevelStr(loglevel)
        self.debug = self.logger.isDebug()

        self._inifile = inifile
        self._haveInitialRemoteConfig = False

        qmlRegisterType(Issue, 'RATT', 1, 0, 'Issue')
        self.loadBootstrapConfig()

        self.remoteConfig = None

    def setNetWorker(self, netWorker=None):
        assert netWorker

        self.remoteConfig = CachedRemoteFile()

        self.remoteConfig.update.connect(self.slotRemoteConfigUpdate)
        self.remoteConfig.updateError.connect(self.slotRemoteConfigUpdateError)

        self.remoteConfig.setup(logger=self.logger, netWorker=netWorker, url=self.config['Auth.ConfigUrl'], cacheFile=self.config['Auth.ConfigCacheFile'])

        self.remoteConfig.download()


    def setMQTT(self, mqtt=None):
        assert mqtt

        self.mqtt = mqtt
        self.mqtt.broadcastEvent.connect(self.__slotBroadcastMQTTEvent)
        self.mqtt.targetedEvent.connect(self.__slotTargetedMQTTEvent)


    @pyqtSlot()
    def slotRemoteConfigUpdate(self):
        self.logger.info('REMOTE CONFIG UPDATE!')
        obj = self.remoteConfig.getObj()
        print obj
        if obj['status'] == 'success':
            p = obj['params']
            for section, params in p.iteritems():
                for key, value in params.iteritems():
                    if type(value) is dict:
                        self.logger.warning('cannot parse dict values in remote config section=%s key=%s -> %s' % (section, key, value))
                    else:
                        self.config['%s.%s' % (section, key)] = value

        #print json.dumps(self.config,2)

        if self.remoteConfig.status != 'same_hash':
            self.configChanged.emit()

        if not self._haveInitialRemoteConfig:
            self._haveInitialRemoteConfig = True
        else:
            if self.mqtt:
                o = { 'status': self.remoteConfig.status, 'source': self.remoteConfig.source, 'hash': self.remoteConfig.hash}
                print o
                self.mqtt.slotPublishSubtopic('config/update', json.dumps(o))



    @pyqtSlot()
    def slotRemoteConfigUpdateError(self):
        self.logger.error('REMOTE CONFIG UPDATE ERROR!')

    # MQTT targeted event
    @pyqtSlot(str, str)
    def __slotTargetedMQTTEvent(self, subtopic, message):
        tsplit = subtopic.split('/')

        if len(tsplit) >= 2 and tsplit[0] == 'config':
            cmd = tsplit[1]

            if cmd == 'update':
                self.remoteConfig.download()

    # MQTT broadcast event
    @pyqtSlot(str, str)
    def __slotBroadcastMQTTEvent(self, subtopic, message):
        tsplit = subtopic.split('/')

        if len(tsplit) >= 2 and tsplit[0] == 'config':
            cmd = tsplit[1]

            if cmd == 'update':
                self.remoteConfig.download()


    #---------------------------------------------------------------------------------------------
    # if any config variables need to be exposed to QML they need to be defined here as properties
    # naming convention to translate from "Section.Key" is to name the property "Section_Key"
    #
    @pyqtProperty(QVariant, notify=configChanged)
    def General_Debug(self):
        return self.config['General.Debug']

    @pyqtProperty(QVariant, notify=configChanged)
    def General_Diags(self):
        return self.config['General.Diags']

    @pyqtProperty(str, notify=configChanged)
    def Personality_Class(self):
        return self.config['Personality.Class']

    @pyqtProperty(int, notify=configChanged)
    def Personality_TimeoutSeconds(self):
        return self.config['Personality.TimeoutSeconds']

    @pyqtProperty(int, notify=configChanged)
    def Personality_TimeoutWarningSeconds(self):
        return self.config['Personality.TimeoutWarningSeconds']

    @pyqtProperty(bool, notify=configChanged)
    def Personality_SafetyCheckEnabled(self):
        return self.config['Personality.SafetyCheckEnabled']

    @pyqtProperty(bool, notify=configChanged)
    def Personality_MonitorToolPowerEnabled(self):
        return self.config['Personality.MonitorToolPowerEnabled']

    @pyqtProperty(bool, notify=configChanged)
    def Personality_HomingManualOverrideEnabled(self):
        return self.config['Personality.HomingManualOverrideEnabled']

    @pyqtProperty(bool, notify=configChanged)
    def Personality_HomingExternalOverrideEnabled(self):
        return self.config['Personality.HomingExternalOverrideEnabled']

    @pyqtProperty(str, notify=configChanged)
    def Personality_Password(self):
        return self.config['Personality.Password']

    @pyqtProperty(str, notify=configChanged)
    def Personality_PasswordPrompt(self):
        return self.config['Personality.PasswordPrompt']

    @pyqtProperty(bool, notify=configChanged)
    def Personality_PasswordEnabled(self):
        return self.config['Personality.PasswordEnabled']

    @pyqtProperty(str, notify=configChanged)
    def Personality_PasswordCorrectText(self):
        return self.config['Personality.PasswordCorrectText']

    @pyqtProperty(str, notify=configChanged)
    def Personality_PasswordIncorrectText(self):
        return self.config['Personality.PasswordIncorrectText']

    @pyqtProperty(bool, notify=configChanged)
    def Personality_AllowForceLogout(self):
        return self.config['Personality.AllowForceLogout']

    @pyqtProperty(str, notify=configChanged)
    def General_ToolDesc(self):
        return self.config['General.ToolDesc']

    @pyqtProperty(int, notify=configChanged)
    def RFID_SimulatedTag(self):
        return self.config['RFID.SimulatedTag']

    @pyqtProperty(bool, notify=configChanged)
    def Sound_EnableSilenceLoop(self):
        return self.config['Sound.EnableSilenceLoop']

    @pyqtProperty(str, notify=configChanged)
    def Sound_Silence(self):
        return self.config['Sound.Silence']

    @pyqtProperty(str, notify=configChanged)
    def Sound_KeyPress(self):
        return self.config['Sound.KeyPress']

    @pyqtProperty(str, notify=configChanged)
    def Sound_GeneralAlert(self):
        return self.config['Sound.GeneralAlert']

    @pyqtProperty(str, notify=configChanged)
    def Sound_RFIDSuccess(self):
        return self.config['Sound.RFIDSuccess']

    @pyqtProperty(str, notify=configChanged)
    def Sound_RFIDFailure(self):
        return self.config['Sound.RFIDFailure']

    @pyqtProperty(str, notify=configChanged)
    def Sound_RFIDError(self):
        return self.config['Sound.RFIDError']

    @pyqtProperty(str, notify=configChanged)
    def Sound_SafetyFailed(self):
        return self.config['Sound.SafetyFailed']

    @pyqtProperty(str, notify=configChanged)
    def Sound_Enable(self):
        return self.config['Sound.Enable']

    @pyqtProperty(str, notify=configChanged)
    def Sound_Disable(self):
        return self.config['Sound.Disable']

    @pyqtProperty(str, notify=configChanged)
    def Sound_TimeoutWarning(self):
        return self.config['Sound.TimeoutWarning']

    @pyqtProperty(str, notify=configChanged)
    def Sound_ReportSuccess(self):
        return self.config['Sound.ReportSuccess']

    @pyqtProperty(str, notify=configChanged)
    def Sound_LiftInstructions(self):
        return self.config['Sound.LiftInstructions']

    @pyqtProperty(str, notify=configChanged)
    def Sound_LiftCorrect(self):
        return self.config['Sound.LiftCorrect']

    @pyqtProperty(str, notify=configChanged)
    def Sound_LiftIncorrect(self):
        return self.config['Sound.LiftIncorrect']

    @pyqtProperty(str, notify=configChanged)
    def Sound_HomingInstructions(self):
        return self.config['Sound.HomingInstructions']

    @pyqtProperty(str, notify=configChanged)
    def Sound_HomingWarning(self):
        return self.config['Sound.HomingWarning']

    @pyqtProperty(str, notify=configChanged)
    def Sound_HomingOverride(self):
        return self.config['Sound.HomingOverride']

    @pyqtProperty(str, notify=configChanged)
    def Issues_Count(self):
        return len(self.parser.items('Issues'))

    @pyqtProperty(QQmlListProperty, notify=configChanged)
    def Issues(self):
        list = [Issue('Exit (no issue to report)')]
        keys = []
        for pair in self.config.items():
            (name, descr) = pair
            if name.startswith('Issues'):
                keys.append(name)

        keys.sort()

        for key in keys:
            descr = self.config[key]
            list.append(Issue(name=descr))

        return QQmlListProperty(Issue, self, list)

    #---------------------------------------------------------------------------------------------

    def value(self, key):
        return self.config[key]

    def addConfig(self, section, key, default=''):
        try:
            self.config['%s.%s' % (section, key)] = self.parser.get(section, key)
        except ConfigParser.NoOptionError:
            self.config['%s.%s' % (section, key)] = default

    def addConfigBool(self, section, key, default=False):
        try:
            self.config['%s.%s' % (section, key)] = self.parser.getboolean(section, key)
        except ConfigParser.NoOptionError:
            self.config['%s.%s' % (section, key)] = default

    def addConfigInt(self, section, key, default=0):
        try:
            self.config['%s.%s' % (section, key)] = self.parser.getint(section, key)
        except ConfigParser.NoOptionError:
            self.config['%s.%s' % (section, key)] = default

    def addConfigFloat(self, section, key, default=0.0):
        try:
            self.config['%s.%s' % (section, key)] = self.parser.getfloat(section, key)
        except ConfigParser.NoOptionError:
            self.config['%s.%s' % (section, key)] = default

    def loadBootstrapConfig(self):
        self.parser = ConfigParser.ConfigParser()

        self.parser.read(self._inifile)

        self.config = { }

        self.addConfigBool('General', 'Diags')
        self.addConfig('General', 'ToolDesc')
        self.addConfig('General', 'NetworkInterfaceName', 'wlan0')
        self.addConfig('General', 'MacAddressOverride', None)

        self.addConfigBool('GPIO', 'Simulated', False)

        self.addConfig('Log', 'File')
        self.addConfigBool('Log', 'Console')
        self.addConfigBool('Log', 'Qt')
        self.addConfigBool('Log', 'QtVerbose')
        self.addConfig('Log', 'LogLevel')

        self.addConfig('Personality', 'Class')
        self.addConfig('Personality', 'LogLevel', 'INFO')
        self.addConfigInt('Personality', 'TimeoutSeconds')
        self.addConfigInt('Personality', 'TimeoutWarningSeconds')
        self.addConfigBool('Personality', 'SafetyCheckEnabled', False)
        self.addConfigBool('Personality', 'MonitorToolPowerEnabled', False)
        self.addConfigBool('Personality', 'HomingManualOverrideEnabled', False)
        self.addConfigBool('Personality', 'HomingExternalOverrideEnabled', False)

        self.addConfigBool('Personality', 'PasswordEnabled', False)
        self.addConfig('Personality', 'Password', 'RATT')
        self.addConfig('Personality', 'PasswordPrompt', 'Password')
        self.addConfig('Personality', 'PasswordCorrectText', 'Thank you, that is correct.')
        self.addConfig('Personality', 'PasswordIncorrectText', 'Sorry, that is incorrect.')
        self.addConfigBool('Personality', 'AllowForceLogout', False)

        self.addConfig('Auth', 'LogLevel', 'INFO')
        self.addConfig('Auth', 'ResourceId')
        self.addConfig('Auth', 'HttpAuthUser')
        self.addConfig('Auth', 'HttpAuthPassword')
        self.addConfig('Auth', 'AclUrl')
        self.addConfig('Auth', 'AclCacheFile')
        self.addConfig('Auth', 'ConfigUrl')
        self.addConfig('Auth', 'ConfigCacheFile')

        self.addConfig('MQTT', 'SSL', False)
        self.addConfig('MQTT', 'LogLevel', 'INFO')
        self.addConfig('MQTT', 'BrokerHost')
        self.addConfigInt('MQTT', 'BrokerPort')
        self.addConfigInt('MQTT', 'ReconnectTime')
        self.addConfig('MQTT', 'BaseTopic')
        self.addConfig('MQTT', 'NodeId', None)

        self.addConfig('Telemetry', 'LogLevel', 'INFO')
        self.addConfig('Telemetry', 'EventUrl')
        self.addConfig('Telemetry', 'EventCacheFile')

        self.addConfigBool('SSL', 'Enabled')
        self.addConfig('SSL', 'CaCertFile')
        self.addConfig('SSL', 'ClientCertFile')
        self.addConfig('SSL', 'ClientKeyFile')

        self.addConfig('RFID', 'LogLevel')
        self.addConfig('RFID', 'SerialPort')
        self.addConfigInt('RFID', 'SimulatedTag', 0)

        self.addConfigBool('Sound', 'EnableSilenceLoop', True)
        self.addConfig('Sound', 'Silence', '')
        self.addConfig('Sound', 'KeyPress', '')
        self.addConfig('Sound', 'GeneralAlert', '')
        self.addConfig('Sound', 'RFIDSuccess', '')
        self.addConfig('Sound', 'RFIDFailure', '')
        self.addConfig('Sound', 'RFIDError', '')
        self.addConfig('Sound', 'SafetyFailed', '')
        self.addConfig('Sound', 'Enable', '')
        self.addConfig('Sound', 'Disable', '')
        self.addConfig('Sound', 'TimeoutWarning', '')
        self.addConfig('Sound', 'ReportSuccess', '')
        self.addConfig('Sound', 'LiftInstructions', '')
        self.addConfig('Sound', 'LiftCorrect', '')
        self.addConfig('Sound', 'LiftIncorrect', '')
        self.addConfig('Sound', 'HomingInstructions', '')
        self.addConfig('Sound', 'HomingWarning', '')
        self.addConfig('Sound', 'HomingOverride', '')

        for i in self.parser.items('Issues'):
            (n, v) = i
            self.addConfig('Issues', n)

        self.configChanged.emit()
