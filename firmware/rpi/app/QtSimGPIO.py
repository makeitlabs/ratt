# Modified to use Qt facilities instead of Twisted
# March 2018 by Steve Richardson (steve.richardson@makeitlabs.com)
#
# Linux SysFS-based native GPIO implementation.
# originally from https://github.com/derekstavis/python-sysfs-gpio
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Derek Willian Stavis
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__all__ = ('DIRECTIONS', 'INPUT', 'OUTPUT',
           'EDGES', 'RISING', 'FALLING', 'BOTH',
           'Controller')

from PyQt5.QtCore import QThread
from Logger import Logger
import logging
import errno
import os
import select

# Sysfs constants

SYSFS_GPIO_VALUE_LOW   = '0'
SYSFS_GPIO_VALUE_HIGH  = '1'

EPOLL_TIMEOUT = 1  # second

# Public interface

INPUT   = 'in'
OUTPUT  = 'out'

RISING  = 'rising'
FALLING = 'falling'
BOTH    = 'both'

ACTIVE_LOW_ON = 1
ACTIVE_LOW_OFF = 0

LOW = False
HIGH = True

DIRECTIONS = (INPUT, OUTPUT)
EDGES = (RISING, FALLING, BOTH)
ACTIVE_LOW_MODES = (ACTIVE_LOW_ON, ACTIVE_LOW_OFF)


class Pin(object):
    # Represent a pin in SysFS

    def __init__(self, number, direction, callback=None, edge=None, active_low=0):
        # @type  number: int
        # @param number: The pin number
        # @type  direction: int
        # @param direction: Pin direction, enumerated by C{Direction}
        # @type  callback: callable
        # @param callback: Method be called when pin changes state
        # @type  edge: int
        # @param edge: The edge transition that triggers callback,
        #              enumerated by C{Edge}
        # @type active_low: int
        # @param active_low: Indicator of whether this pin uses inverted
        #                    logic for HIGH-LOW transitions.
        self._number = number
        self._direction = direction
        self._callback  = callback
        self._active_low = active_low

        self._val = 0
        
        if callback and not edge:
            raise Exception('You must supply a edge to trigger callback on')

    @property
    def callback(self):
        # Gets this pin callback
        return self._callback

    @callback.setter
    def callback(self, value):
        # Sets this pin callback
        self._callback = value

    @property
    def direction(self):
        # Pin direction
        return self._direction

    @property
    def number(self):
        # Pin number
        return self._number

    @property
    def active_low(self):
        # Pin active logic
        return self._active_low

    def set(self, value):
        print('set pin=' + str(self._number) + ' value=' + str(value))

    def get (self):
        return int(self._val)

    def fileno(self):
        # Get the file descriptor associated with this pin.
        #
        # @rtype: int
        # @return: File descriptor
        return -1

    def changed(self, state):
        if callable(self._callback):
            self._callback(self.number, state)


class Controller(QThread):
    # A class to provide access to SysFS GPIO pins
    def __init__(self, loglevel='DEBUG'):
        QThread.__init__(self)
        self.logger = Logger(name='ratt.qsimgpio')
        self.logger.setLogLevelStr(loglevel)
        self.debug = self.logger.isDebug()

        self._allocated_pins = {}
        self._available_pins = []
        self._running = True

        self.start()

    def run(self):
        self.logger.debug('running')

        while self._running:
            self.sleep(1)

    @property
    def available_pins(self):
        return self._available_pins

    @available_pins.setter
    def available_pins(self, value):
        self._available_pins = value

    def stop(self):
        self._running = False

        try:
            values = self._allocated_pins.copy().itervalues()
        except AttributeError:
            values = self._allocated_pins.copy().values()
        for pin in values:
            self.dealloc_pin(pin.number)

    def alloc_pin(self, number, direction, callback=None, edge=None, active_low=0):

        self.logger.debug('alloc_pin(%d, %s, %s, %s, %s)'
                     % (number, direction, callback, edge, active_low))

        if direction not in DIRECTIONS:
            raise Exception("Pin direction %s not in %s"
                            % (direction, DIRECTIONS))

        if callback and edge not in EDGES:
            raise Exception("Pin edge %s not in %s" % (edge, EDGES))

        pin = Pin(number, direction, callback, edge, active_low)

        self._allocated_pins[number] = pin
        return pin


    def dealloc_pin(self, number):

        self.logger.debug('dealloc_pin(%d)' % number)

        if number not in self._allocated_pins:
            raise Exception('Pin %d not allocated' % number)

        with open(SYSFS_UNEXPORT_PATH, 'w') as unexport:
            unexport.write('%d' % number)

        pin = self._allocated_pins[number]

        del pin, self._allocated_pins[number]

    def get_pin(self, number):

        self.logger.debug('get_pin(%d)' % number)

        return self._allocated_pins[number]

    def set_pin(self, number):

        self.logger.debug('set_pin(%d)' % number)

        if number not in self._allocated_pins:
            raise Exception('Pin %d not allocated' % number)

        return self._allocated_pins[number].set()

    def reset_pin(self, number):

        self.logger.debug('reset_pin(%d)' % number)

        if number not in self._allocated_pins:
            raise Exception('Pin %d not allocated' % number)

        return self._allocated_pins[number].reset()

    def get_pin_state(self, number):

        self.logger.debug('get_pin_state(%d)' % number)

        if number not in self._allocated_pins:
            raise Exception('Pin %d not allocated' % number)

        pin = self._allocated_pins[number]

        val = pin.get()

        if val <= 0:
            return False
        else:
            return True


if __name__ == '__main__':
    print("This module isn't intended to be run directly.")
