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

from PyQt5.QtCore import Qt, QThread, QWaitCondition, QMutex, QIODevice, QByteArray, pyqtSlot, pyqtSignal, pyqtProperty
from PyQt5.QtSerialPort import QSerialPort
from Logger import Logger
import logging
import calendar
import time
import hashlib
import queue

class RFID(QThread):
    tagScan = pyqtSignal(int, str, int, str, name='tagScan', arguments=['tag', 'hash', 'time', 'debugText'])
    tagScanError = pyqtSignal(int, int, str, name='tagScanError', arguments=['error', 'time', 'debugText'])

    @pyqtProperty(int)
    def errPacket(self):
        return -1

    @pyqtProperty(int)
    def errChecksum(self):
        return -2

    @pyqtSlot(int)
    def simulateTagScan(self, tag):
        hash = self.hash_tag(tag)
        now = calendar.timegm(time.gmtime())
        self.tagScan.emit(tag, hash, now, 'simulated')

    @pyqtSlot()
    def simulateScanError(self):
        now = calendar.timegm(time.gmtime())
        self.tagScanError.emit(0, now, 'simulated')

    def __init__(self, portName='', baudRate=QSerialPort.Baud9600, loglevel='WARNING'):
        QThread.__init__(self)

        self.logger = Logger(name='ratt.rfid')
        self.logger.setLogLevelStr(loglevel)
        self.debug = self.logger.isDebug()

        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.portName = portName
        self.baudRate = baudRate
        self.waitTimeout = 250

        self.quit = False

        self.outQueue = queue.Queue()

    def serialOut(self, msg):
        self.mutex.lock()
        self.outQueue.put(msg)
        self.mutex.unlock()

    def monitor(self):
        if not self.isRunning():
            self.start();
        else:
            self.cond.wakeOne();

    def dump_pkt(self, bytes):
        bstr = ''
        for b in bytes:
            byte = ord(b)
            bstr += '%02x ' % byte

        return bstr


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
                self.logger.debug('calc checksum byte %d (%2x), checksum = %2x' % (i, ord(bytes[i]), checksum))

            if checksum == 0:
                tag = (ord(bytes[4]) << 24) | (ord(bytes[5]) << 16) | (ord(bytes[6]) << 8) | ord(bytes[7])

                self.logger.debug("serial read: " + self.dump_pkt(bytes))
                self.logger.debug('tag = %10.10d' % tag)

                return tag

            else:
                self.logger.warning("checksum error")
                return self.errChecksum
        else:
            self.logger.warning("packet error")
            return self.errPacket

    def hash_tag(self, tag):
        m = hashlib.sha224()
        tag_str = '%.10d' % int(tag)
        m.update(str(tag_str).encode())
        tag_hash = m.hexdigest()

        self.logger.debug('hash: %s' % tag_hash)

        return tag_hash

    def run(self):
        self.serial = QSerialPort()
        self.serial.setPortName(self.portName)
        self.serial.setBaudRate(self.baudRate)

        # open read-write for serial output function, which is unrelated to RFID,
        # but lives here because the port can only be opened in one place
        if not self.serial.open(QIODevice.ReadWrite):
            self.logger.error("can't open serial port")
            return;

        while not self.quit:
            # look for queued serial output items, write them to serial port
            writeItem = None
            self.mutex.lock()
            if not self.outQueue.empty():
                writeItem = self.outQueue.get()
                self.outQueue.task_done()
            self.mutex.unlock()

            if self.serial.isWritable() and writeItem is not None:
                self.logger.debug('writing msg to serial: %s' % writeItem)
                self.serial.writeData(writeItem.encode("utf-8"))

            # look for incoming data from RFID module, read and process it
            if self.serial.waitForReadyRead(self.waitTimeout):
                bytes = self.serial.readAll()

                while self.serial.waitForReadyRead(10):
                    bytes += self.serial.readAll()

                tag = self.decode_gwiot(bytes)
                now = calendar.timegm(time.gmtime())

                self.logger.debug("tag=%d, now=%d" % (tag, now))

                if tag > 0:
                    self.tagScan.emit(tag, self.hash_tag(tag), now, self.dump_pkt(bytes))
                else:
                    self.tagScanError.emit(tag, now, self.dump_pkt(bytes))
