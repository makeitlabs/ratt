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
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, pyqtProperty
import logging

class SignalStreamHandler(QObject, logging.StreamHandler):
    logEvent = pyqtSignal(str, name='logEvent', arguments=['text'])

    def __init__(self):
        QObject.__init__(self)
        logging.StreamHandler.__init__(self)

        fmt = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
        self.setFormatter(fmt)

    def emit(self, record):
        self.logEvent.emit(self.format(record))


class Logger(QObject):

    @pyqtProperty(QObject)
    def signalStreamHandler(self):
        if self.sig:
            print("***")
            print(self.sig)
            return self.sig

        return None

    def __init__(self, name, filename='', stream=False,
                 flevel=logging.INFO, slevel=logging.DEBUG, mlevel=logging.NOTSET,
                 qt=False, qtlevel=logging.INFO, qtVerbose=False):

        QObject.__init__(self)
        self.log = logging.getLogger(name)
        self.log.setLevel(mlevel)

        # create a logfile handler only if filename is set
        if filename != '':
            self.handler = logging.FileHandler(filename)

            fmt = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
            self.handler.setFormatter(fmt)

            self.handler.setLevel(flevel)
            self.log.addHandler(self.handler)

        # create a stream stdout handler only if enabled
        if stream:
            self.console = logging.StreamHandler()
            self.console.setLevel(slevel)
            fmt = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
            self.console.setFormatter(fmt)
            logging.getLogger('').addHandler(self.console)

            self.sig = SignalStreamHandler()
            self.sig.setLevel(slevel)
            logging.getLogger('').addHandler(self.sig)

        # install Qt handler if enabled
        if qt:
            self.qtlog = logging.getLogger(name + '.qt')
            self.qtlog.setLevel(qtlevel)
            if qtVerbose:
                qInstallMessageHandler(self.qtVerboseDebugHandler)
            else:
                qInstallMessageHandler(self.qtDebugHandler)


    def setLogLevelStr(self, levelstr, fallback=logging.WARNING):
        try:
            loglevel = eval('logging.' + levelstr)
            self.log.setLevel(loglevel)
            return True
        except:
            self.log.setLevel(fallback)
            return False

    def isDebug(self):
        dbg = bool(self.log.getEffectiveLevel() == logging.DEBUG)
        if dbg:
            self.log.debug("debug enabled")
        return dbg




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
        if mode == QtInfoMsg:
            self.qtlog.info(message)
        elif mode == QtWarningMsg:
            self.qtlog.warning(message)
        elif mode == QtCriticalMsg:
            self.qtlog.critical(message)
        elif mode == QtFatalMsg:
            self.qtlog.error(message)
        else:
            self.qtlog.debug(message)

    def qtVerboseDebugHandler(self, mode, context, message):
        msg = '[line %d, func %s(), file %s]: %s' % (context.line, context.function, context.file, message)

        if mode == QtInfoMsg:
            self.qtlog.info(msg)
        elif mode == QtWarningMsg:
            self.qtlog.warning(msg)
        elif mode == QtCriticalMsg:
            self.qtlog.critical(msg)
        elif mode == QtFatalMsg:
            self.qtlog.error(msg)
        else:
            self.qtlog.debug(msg)
