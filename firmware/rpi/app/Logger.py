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

    def info(self, msg, *args, **kwargs):
        self.log.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.log.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.log.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.log.exception(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.log.debug(msg, *args, **kwargs)

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
