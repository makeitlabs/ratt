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
import ConfigParser

RATT_INI_FILE = '/data/ratt/ratt.ini'

class RattConfig(QObject):
    configChanged = pyqtSignal()

    def __init__(self):
        QObject.__init__(self)
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

    @pyqtProperty(str, notify=configChanged)
    def General_ToolDesc(self):
        return self.config['General.ToolDesc']

    @pyqtProperty(str, notify=configChanged)
    def Sound_Silence(self):
        return self.config['Sound.Silence']

    @pyqtProperty(str, notify=configChanged)
    def Sound_KeyPress(self):
        return self.config['Sound.KeyPress']

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

    #---------------------------------------------------------------------------------------------



    def value(self, key):
        return self.config[key]

    def addConfig(self, section, key):
        self.config['%s.%s' % (section, key)] = self.parser.get(section, key)

    def addConfigBool(self, section, key):
            self.config['%s.%s' % (section, key)] = self.parser.getboolean(section, key)

    def addConfigInt(self, section, key):
            self.config['%s.%s' % (section, key)] = self.parser.getint(section, key)

    def addConfigFloat(self, section, key):
            self.config['%s.%s' % (section, key)] = self.parser.getfloat(section, key)

    def loadConfig(self):
        self.parser = ConfigParser.ConfigParser()

        self.parser.read(RATT_INI_FILE)

        self.config = { }

        self.addConfigBool('General', 'Diags')
        self.addConfig('General', 'ToolDesc')

        self.addConfig('Log', 'File')
        self.addConfigBool('Log', 'Console')
        self.addConfigBool('Log', 'Qt')
        self.addConfigBool('Log', 'QtVerbose')
        self.addConfig('Log', 'LogLevel')

        self.addConfig('Personality', 'Class')
        self.addConfig('Personality', 'LogLevel')
        self.addConfigInt('Personality', 'TimeoutSeconds')
        self.addConfigInt('Personality', 'TimeoutWarningSeconds')

        self.addConfig('Auth', 'LogLevel')
        self.addConfig('Auth', 'ResourceId')
        self.addConfig('Auth', 'HttpAuthUser')
        self.addConfig('Auth', 'HttpAuthPassword')
        self.addConfig('Auth', 'AclUrl')
        self.addConfig('Auth', 'AclCacheFile')

        self.addConfig('MQTT', 'LogLevel')
        self.addConfig('MQTT', 'BrokerHost')
        self.addConfigInt('MQTT', 'BrokerPort')
        self.addConfigInt('MQTT', 'ReconnectTime')
        self.addConfig('MQTT', 'BaseTopic')

        self.addConfig('Telemetry', 'LogLevel')
        self.addConfig('Telemetry', 'EventUrl')
        self.addConfig('Telemetry', 'EventCacheFile')

        self.addConfigBool('SSL', 'Enabled')
        self.addConfig('SSL', 'CaCertFile')
        self.addConfig('SSL', 'ClientCertFile')
        self.addConfig('SSL', 'ClientKeyFile')

        self.addConfig('RFID', 'LogLevel')
        self.addConfig('RFID', 'SerialPort')

        self.addConfig('Sound', 'Silence')
        self.addConfig('Sound', 'KeyPress')
        self.addConfig('Sound', 'RFIDSuccess')
        self.addConfig('Sound', 'RFIDFailure')
        self.addConfig('Sound', 'RFIDError')
        self.addConfig('Sound', 'SafetyFailed')
        self.addConfig('Sound', 'Enable')
        self.addConfig('Sound', 'Disable')
        self.addConfig('Sound', 'TimeoutWarning')
        self.addConfig('Sound', 'ReportSuccess')

        self.configChanged.emit()
