# -*- coding: utf-8 -*-
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

from PyQt5.QtCore import Qt, QThread, QWaitCondition, QMutex, QIODevice, QByteArray, pyqtSignal
from PyQt5.QtSerialPort import QSerialPort
import calendar
import time

class RFID(QThread):
    tagScan = pyqtSignal(int, int, name='tagScan', arguments=['tag', 'time'])
    tagScanError = pyqtSignal(int, name='tagScanError', arguments=['time'])

    def __init__(self, portName):
        QThread.__init__(self)

        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.portName = portName
        self.waitTimeout = 250

        self.debug = False

        self.quit = False

    def monitor(self):
        if not self.isRunning():
            self.start();
        else:
            self.cond.wakeOne();

    def decode_gwiot(self, bytes):
        #
        # sample packet from "Gwiot 7941e V3.0" eBay RFID module:
        #
        # 00   01   02   03   04   05   06   07   08   09   BYTE #
        # -----------------------------------------------------------
        # 02   0A   02   11   00   0D   EF   80   7B   03
        # |    |    |    |    |    |    |    |    |    |
        # STX  ??   ??   ??   id3  id2  id1  id0  sum  ETX
        #
        # checksum (byte 8, 'sum') is a simple 8-bit XOR of bytes 01 through 07
        # starting the checksum with the value of 'sum' or starting with 0 and
        # including the value of 'sum' in the calculation will net a checksum
        # value of 0 when correct
        #
        # the actual tag value is contained in bytes 04 through 07 as a 32-bit
        # unsigned integer.  byte 04 ('id3') is the most significant byte, while
        # byte 07 ('id0') is the least significant byte.
        #
        if bytes.length() == 10 and ord(bytes[0]) == 0x02 and ord(bytes[9]) == 0x03:
            checksum = ord(bytes[8])
            for i in range(1, 8):
                checksum = checksum ^ ord(bytes[i])
                if self.debug:
                    print('rfid calc checksum byte %d (%2x), checksum = %2x' % (i, ord(bytes[i]), checksum))

            if checksum == 0:
                tag = (ord(bytes[4]) << 24) | (ord(bytes[5]) << 16) | (ord(bytes[6]) << 8) | ord(bytes[7])

                if self.debug:
                    bstr = ''
                    for b in bytes:
                        byte = ord(b)
                        bstr += '%02x ' % byte

                    print("rfid serial read: " + bstr)
                    print('rfid tag = %10.10d' % tag)

                return tag

            else:
                print("rfid: checksum error")
                return -2
        else:
            print("rfid: packet error")
            return -1

    def run(self):

        serial = QSerialPort()
        serial.setPortName(self.portName)

        if not serial.open(QIODevice.ReadOnly):
            print("rfid: can't open serial port")
            return;

        while not self.quit:
            if serial.waitForReadyRead(self.waitTimeout):
                bytes = serial.readAll()

                while serial.waitForReadyRead(10):
                    bytes += serial.readAll()

                tag = self.decode_gwiot(bytes)

                if tag > 0:
                    self.tagScan.emit(tag, calendar.timegm(time.gmtime()))
                else:
                    self.tagScanError.emit(calendar.timegm(time.gmtime()))
