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

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty

class MemberRecord(QObject):
    recordChanged = pyqtSignal()

    def __init__(self, initRecord = []):
        QObject.__init__(self)
        self.clear()

        if initRecord != []:
            self.parseRecord(initRecord)

    def copy(self, source):
        self._member = source.name
        self._nickname = source.nickname
        self._level = source.level
        self._tagid = source.tag
        self._lastaccessed = source.lastAccessed
        self._warning = source.warningText
        self._plan = source.plan
        self._allowed = source.allowed
        self._isValid = source.valid
        self.recordChanged.emit()


    def clear(self):
        self._member = ''
        self._nickname = ''
        self._level = -1
        self._tagid = ''
        self._lastaccessed = ''
        self._warning = ''
        self._plan = ''
        self._allowed = False
        self._isValid = False
        self.recordChanged.emit()

    def parseRecord(self, record):
        try:
            self._member = record['member']
            self._nickname = record['nickname']
            self._level = int(record['level'])
            self._tagid = record['tagid']
            self._lastaccessed = record['last_accessed']
            self._warning = record['warning']
            self._plan = record['plan']
            self._allowed = (record['allowed'] == 'allowed')
            self._isValid = True
            self.recordChanged.emit()

        except:
            self.clear()

        return self._isValid


    @pyqtProperty(str, notify=recordChanged)
    def name(self):
        return self._member

    @pyqtProperty(str, notify=recordChanged)
    def nickname(self):
        return self._nickname

    @pyqtProperty(int, notify=recordChanged)
    def level(self):
        return self._level

    @pyqtProperty(str, notify=recordChanged)
    def tag(self):
        return self._tagid

    @pyqtProperty(str, notify=recordChanged)
    def lastAccessed(self):
        return self._lastaccessed

    @pyqtProperty(str, notify=recordChanged)
    def warningText(self):
        return self._warning

    @pyqtProperty(str, notify=recordChanged)
    def plan(self):
        return self._plan

    @pyqtProperty(bool, notify=recordChanged)
    def allowed(self):
        return self._allowed

    @pyqtProperty(bool, notify=recordChanged)
    def valid(self):
        return self._isValid
