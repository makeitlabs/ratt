# -*- coding: utf-8 -*-


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

    def transaction(self):
        if not self.isRunning():
            self.start();
        else:
            self.cond.wakeOne();

    def run(self):

        serial = QSerialPort()
        serial.setPortName(self.portName)

        if not serial.open(QIODevice.ReadOnly):
            print("can't open serial port")
            return;

        while not self.quit:
            if serial.waitForReadyRead(self.waitTimeout):
                bytes = serial.readAll()

                while serial.waitForReadyRead(10):
                    bytes += serial.readAll()


                # sample packet from RFID module:
                #
                # 00   01   02   03   04   05   06   07   08   09   BYTE #
                # -----------------------------------------------------------
                # 02   0A   02   11   00   0D   EF   80   7B   03
                # |    |    |    |    |    |    |    |    |    |
                # STX  ??   ??   ??   id3  id2  id1  id0  sum  ETX
                #
                # checksum (byte 8, 'sum') is a simple 8-bit XOR of bytes 2 through 8
                # starting the XORing with the value of 'sum' or starting with 0 and
                # including the value of 'sum' will net a checksum value of 0 when correct
                #
                #
                if bytes.length() == 10 and ord(bytes[0]) == 0x02 and ord(bytes[9]) == 0x03:
                    checksum = ord(bytes[8])
                    for i in range(1, 8):
                        checksum = checksum ^ ord(bytes[i])
                        if self.debug:
                            print('calc checksum byte %d (%2x), checksum = %2x' % (i, ord(bytes[i]), checksum))

                    if checksum == 0:
                        tag = (ord(bytes[4]) << 24) | (ord(bytes[5]) << 16) | (ord(bytes[6]) << 8) | ord(bytes[7])

                        self.tagScan.emit(tag, calendar.timegm(time.gmtime()))

                        if self.debug:
                            bstr = ''
                            for b in bytes:
                                byte = ord(b)
                                bstr += '%02x ' % byte

                            print("serial read: " + bstr)
                            print('tag = %10.10d' % tag)

                    else:
                        print("checksum error")

