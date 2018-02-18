#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl, qInstallMessageHandler
from PyQt5.QtCore import qDebug, QtInfoMsg, QtWarningMsg, QtCriticalMsg, QtFatalMsg
from RattAppEngine import RattAppEngine

def qtDebugHandler(mode, context, message):
    if mode == QtInfoMsg:
        mode = 'INFO'
    elif mode == QtWarningMsg:
        mode = 'WARNING'
    elif mode == QtCriticalMsg:
        mode = 'CRITICAL'
    elif mode == QtFatalMsg:
        mode = 'FATAL'
    else:
        mode = 'DEBUG'
        print('qt_message_handler: line: %d, func: %s(), file: %s' % (context.line, context.function, context.file))

    print('  %s: %s' % (mode, message))


if __name__ == '__main__':
    qInstallMessageHandler(qtDebugHandler)
    app = QGuiApplication(sys.argv)
    engine = RattAppEngine()
    engine.load(QUrl('main.qml'))
    engine.quit.connect(app.quit)
    sys.exit(app.exec_())
