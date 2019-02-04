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

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty, QVariant
from PyQt5.QtQml import QQmlListProperty, qmlRegisterType
import ConfigParser

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

    def __init__(self, inifile):
        QObject.__init__(self)

        self._inifile = inifile

        qmlRegisterType(Issue, 'RATT', 1, 0, 'Channel')
        self.loadConfig()

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
        for pair in self.parser.items('Issues'):
            (name, descr) = pair
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

    def loadConfig(self):
        self.parser = ConfigParser.ConfigParser()

        self.parser.read(self._inifile)

        self.config = { }

        self.addConfigBool('General', 'Diags')
        self.addConfig('General', 'ToolDesc')
        self.addConfig('General', 'NetworkInterfaceName', 'wlan0')

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
