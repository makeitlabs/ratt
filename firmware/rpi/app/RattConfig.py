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

    @pyqtProperty(str, notify=configChanged)
    def General_ToolDesc(self):
        return self.config['General.ToolDesc']

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
        defaults = {}
        self.parser = ConfigParser.ConfigParser(defaults)
        self.parser.read('ratt.ini')

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

        self.addConfig('Auth', 'LogLevel')
        self.addConfig('Auth', 'ResourceId')
        self.addConfig('Auth', 'AclUrl')
        self.addConfig('Auth', 'LogUrl')
        self.addConfig('Auth', 'HttpAuthUser')
        self.addConfig('Auth', 'HttpAuthPassword')

        self.addConfigBool('SSL', 'Enabled')
        self.addConfig('SSL', 'CaCertFile')
        self.addConfig('SSL', 'ClientCertFile')
        self.addConfig('SSL', 'ClientKeyFile')

        self.addConfig('RFID', 'LogLevel')
        self.addConfig('RFID', 'SerialPort')

        self.addConfig('Sound', 'KeyPress')
        self.addConfig('Sound', 'RFIDSuccess')
        self.addConfig('Sound', 'RFIDFailure')
        self.addConfig('Sound', 'RFIDError')

        self.configChanged.emit()






