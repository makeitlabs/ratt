#!/usr/bin/env python
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

import sys
from PyQt5.QtGui import QGuiApplication, QFont
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
from RattAppEngine import RattAppEngine


class MainApp(QObject):
    app = None
    engine = None

    def __init__(self):
        QObject.__init__(self)
        self.enableBacklight()
        self.createApp()
        self.createEngine()

    def enableBacklight(self):
        try:
            # turn on backlight
            fd = open('/sys/class/backlight/fb_st7735r/bl_power', 'w+')
            fd.write('0')
            fd.close()
        except:
            pass

    def createApp(self):
        if not self.app:
            self.app = QGuiApplication(sys.argv)

            # Available fonts on RATT image:
            # AR PL UMing CN, AR PL UMing HK, AR PL UMing TW, AR PL UMing TW MBE,
            # Bitstream Vera Sans, Bitstream Vera Sans Mono, Bitstream Vera Serif,
            # DejaVu Sans, DejaVu Sans Condensed, DejaVu Sans Mono,
            # Liberation Mono, Liberation Sans,
            # Monospace, Sans Serif, Serif,
            # Sazanami Gothic, Sazanami Mincho,
            # Ubuntu, Ubuntu Condensed, Ubuntu Light,Ubuntu Mono
            font = QFont("Ubuntu", 12)
            self.app.setFont(font)

    def createEngine(self):
        if not self.engine:
            print("creating engine")
            self.engine = RattAppEngine()
            self.engine.load(QUrl('main.qml'))
            self.engine.exit.connect(self.exit)

    @pyqtSlot(int)
    def exit(self, exitCode):
        print "exit, code=", exitCode
        if exitCode == 2 and self.engine:
            print "reloading qml"
            self.engine.load(QUrl('main.qml'))

    def run(self):
        return self.app.exec_()

    def cleanup(self):
        del self.engine
        del self.app


if __name__ == '__main__':
    ma = MainApp()
    running = True
    while running:
        print "running"
        r = ma.run()
        print "done r=", r
        if r != 2:
            running = False

    ma.cleanup()
    del ma
    sys.exit(r)
