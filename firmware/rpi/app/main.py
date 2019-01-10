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

if __name__ == '__main__':
    try:
        # turn on backlight
        fd = open('/sys/class/backlight/fb_st7735r/bl_power', 'w+')
        fd.write('1')
        fd.close()
    except:
        pass

    app = QGuiApplication(sys.argv)

    # Available fonts on RATT image:
    # AR PL UMing CN, AR PL UMing HK, AR PL UMing TW, AR PL UMing TW MBE,
    # Bitstream Vera Sans, Bitstream Vera Sans Mono, Bitstream Vera Serif,
    # DejaVu Sans, DejaVu Sans Condensed, DejaVu Sans Mono,
    # Liberation Mono, Liberation Sans,
    # Monospace, Sans Serif, Serif,
    # Sazanami Gothic, Sazanami Mincho,
    # Ubuntu, Ubuntu Condensed, Ubuntu Light,Ubuntu Mono
    font = QFont("Ubuntu", 12)
    app.setFont(font)


    engine = RattAppEngine()
    engine.load(QUrl('main.qml'))
    engine.quit.connect(app.quit)

    sys.exit(app.exec_())
