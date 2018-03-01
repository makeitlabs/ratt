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

from PyQt5.QtCore import qInstallMessageHandler
from PyQt5.QtCore import qDebug, QtInfoMsg, QtWarningMsg, QtCriticalMsg, QtFatalMsg
import logging

class Logger():
    def __init__(self, name='Logger', filename='logger.log'):
        qInstallMessageHandler(self.qtDebugHandler)

        self.log = logging.getLogger(name)

        self.handler = logging.FileHandler(filename)

        fmt = logging.Formatter('%(asctime)s: %(levelname)s %(message)s')
        self.handler.setFormatter(fmt)

        self.handler.setLevel(logging.INFO)
        self.log.addHandler(self.handler)


        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        fmt = logging.Formatter('%(name)s: %(levelname)-8s %(message)s')
        console.setFormatter(fmt)
        logging.getLogger('').addHandler(console)

        self.log.setLevel(logging.DEBUG)

    def info(self, msg):
        self.log.info(msg)

    def warning(self, msg):
        self.log.warning(msg)

    def error(self, msg):
        self.log.error(msg)

    def critical(self, msg):
        self.log.critical(msg)

    def exception(self, msg):
        self.log.exception(msg)

    def debug(self, msg):
        self.log.debug(msg)

    def qtDebugHandler(self, mode, context, message):
        msg = '(Qt line: %d, func: %s(), file: %s): %s' % (context.line, context.function, context.file, message)

        if mode == QtInfoMsg:
            self.info(msg)
        elif mode == QtWarningMsg:
            self.warning(msg)
        elif mode == QtCriticalMsg:
            self.critical(msg)
        elif mode == QtFatalMsg:
            self.error(msg)
        else:
            self.debug(msg)
