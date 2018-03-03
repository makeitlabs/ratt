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
# copy of this software and assoceiated documentation files (the "Software"),
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

from PyQt5.QtCore import QObject, QThread, QMutex, QWaitCondition, QTimer
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty, QVariant
from Logger import Logger
from MemberRecord import MemberRecord
import QtGPIO as GPIO


class PersonalityBase(QThread):
    PERSONALITY_DESCRIPTION = 'Base'

    PHASE_ENTER = 0
    PHASE_ACTIVE = 1
    PHASE_EXIT = 100

    phaseLookup = { PHASE_ENTER : 'ENTER', PHASE_ACTIVE : 'ACTIVE', PHASE_EXIT : 'EXIT' }

    REASON_NONE = 0
    REASON_TIMEOUT = 1
    REASON_TIMER = 2
    REASON_GPIO = 3
    REASON_VALID_SCAN = 4
    REASON_INVALID_SCAN = 5

    reasonLookup = { REASON_NONE : 'NONE', REASON_TIMEOUT : 'TIMEOUT', REASON_TIMER : 'TIMER',
                     REASON_GPIO : 'GPIO' , REASON_VALID_SCAN : 'VALID_SCAN', REASON_INVALID_SCAN : 'INVALID_SCAN'}

    stateChanged = pyqtSignal(str, int, name='stateChanged', arguments=['state', 'phase'])
    pinChanged = pyqtSignal(int, int, name='pinChanged', arguments=['pin', 'state'])

    timerStart = pyqtSignal(int, name='timerStart', arguments=['msec'])
    timerStop = pyqtSignal()

    @pyqtProperty(str, notify=stateChanged)
    def currentState(self):
        return self.stateName()

    def __init__(self, loglevel='WARNING', app=None):
        QThread.__init__(self)

        self.cond = QWaitCondition()
        self.mutex = QMutex()

        self.logger = Logger(name='ratt.personality')
        self.logger.setLogLevelStr(loglevel)

        self.logger.info('Personality is ' + self.descr())
        self.debug = self.logger.isDebug()

        if app is None:
            self.logger.error('must set app to QQmlApplicationEngine object')
            exit(-1)

        self.app = app

        self.quit = False

        self.state = None
        self.statePhase = None

        self.wakereason = self.REASON_NONE

        self.timer = QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.__timerTick)

        self.timerStart.connect(self.timer.start)
        self.timerStop.connect(self.timer.stop)

        self.__init_gpio()

    def descr(self):
        return self.PERSONALITY_DESCRIPTION


    # returns specified state/phase as a human-friendly string
    # if state/phase not specified, will return the current state/phase string
    def stateName(self, state = None, phase = None):
        if state == None or phase == None:
            state = self.state
            phase = self.statePhase

        if phase in self.phaseLookup:
            pname = self.phaseLookup[phase]
        elif phase >= self.PHASE_ACTIVE and phase < self.PHASE_EXIT:
            pname = '%s.%d' % (self.phaseLookup[self.PHASE_ACTIVE], phase - self.PHASE_ACTIVE)

        return '%s.%s' % (state, pname)

    # returns the specified wake reason as a human-friendly string, or will return the current wakereason string
    def reasonName(self, reason = None):
        if reason == None:
            reason = self.wakereason

        return self.reasonLookup[reason]

    # execute a state change to the specified state and phase
    # emits the stateChanged signal upon change
    def setState(self, state, phase):
        if state in self.states:
            if state != self.state or phase != self.statePhase:
                self.logger.debug('setState %s ==> %s' % (self.stateName(self.state, self.statePhase), self.stateName(state, phase)))
                self.state = state
                self.statePhase = phase

                self.stateChanged.emit(self.state, self.statePhase)
                return True
            else:
                self.logger.warning('tried to change to current state %s' % self.stateName(state, phase))
        else:
            self.logger.error('invalid state (%s)' % state)

        return False

    # store a state/phase for later use, typically for storing where to go after exiting current state
    def setNextState(self, state, phase):
        if state in self.states:
            if state != self.state or phase != self.statePhase:
                self.logger.debug('setNextState %s' % self.stateName(state, phase))
                self.nextState = state
                self.nextStatePhase = phase
                return True
            else:
                self.logger.warning('tried to set next state to current state %s' % self.stateName(state, phase))
        else:
            self.logger.error('invalid state (%s)' % state)

        return False

    # execute a state change to the stored next state/next phase
    # emits the stateChanged signal upon change
    def goNextState(self):
        self.logger.debug('goNextState %s ==> %s' % (self.stateName(self.state, self.statePhase), self.stateName(self.nextState, self.nextStatePhase)))
        self.state = self.nextState
        self.statePhase = self.nextStatePhase
        self.stateChanged.emit(self.state, self.statePhase)
        return True

    # shortcut to set the enter phase of the next state and exits the current state through its exit phase
    # (assumes the exit phase will transition to the next state)
    # returns True on success
    def exitAndGoto(self, state):
        return self.setNextState(state, self.PHASE_ENTER) and self.setState(self.state, self.PHASE_EXIT)

    # shortcut to directly go to a new state through its enter phase
    def goto(self, state):
        return self.setState(state, self.PHASE_ENTER)

    # shortcut to directly go to the current state active phase (plus an optional active phase offset)
    def goActive(self, active_phase = 0):
        return self.setState(self.state, self.PHASE_ACTIVE + active_phase)

    # shortcut conditional for PHASE_ENTER
    @property
    def phENTER(self):
        return self.statePhase is self.PHASE_ENTER

    # shortcut conditional for PHASE_ACTIVE
    @property
    def phACTIVE(self):
        return self.statePhase is self.PHASE_ACTIVE

    # shortcut conditional for PHASE_ACTIVE with an optional active phase offset
    def phACTIVEn(self, active_phase = 0):
        return self.statePhase is (self.PHASE_ACTIVE + active_phase)

    # shortcut conditional for PHASE_EXIT
    @property
    def phEXIT(self):
        return self.statePhase is self.PHASE_EXIT


    def execute(self):
        if not self.isRunning():
            self.start();

    def run(self):
        self.logger.debug('thread run')

        self.setState(self.STATE_INIT, 0)

        # initialize by running through the initial states and phases until a False is returned
        again = True
        while again:
            curStateFunc = self.states[self.state]
            again = curStateFunc()

        # main thread loop
        while not self.quit:
            # go to sleep until something interesting happens (RFID, GPIO, timeouts, etc)
            # wait will release the lock on the mutex while it waits, but it won't wait if it isn't locked
            # when it stops waiting we'll have the lock again
            self.mutex.lock()
            self.cond.wait(self.mutex)

            self.logger.debug('%s woke up because %s' % (self.stateName(), self.reasonName()))

            # run the state machine until a False is returned (meaning go back to waiting)
            again = True
            while again:
                curStateFunc = self.states[self.state]
                again = curStateFunc()
                self.wakereason = self.REASON_NONE

            self.mutex.unlock()



    # gpio initialization
    def __init_gpio(self):
        self.gpio = GPIO.Controller()
        self.pins = []
        self._init_gpio_pins()

    # this is the callback for when one of the specified GPIO input pins has changed state
    # it wakes the thread with REASON_GPIO
    def __pinchanged(self, num, state):
        self.mutex.lock()
        self.wakereason = self.REASON_GPIO
        self.mutex.unlock()
        self.cond.wakeAll()

    #-----------------------------------------------------------------------------------------
    # on the RATT platform the 16-bit I/O expander appears as /sys/class/gpio/gpiochip496
    # the first 8 gpios are used for personality implementation (motor control, sensing, etc.)
    #
    # in most configurations the hardware forces 496..499 as inputs and 500..503 as outputs
    # it is technically possible to use these in other configurations via the 2x8 I/O header
    # since it just exposes the expander pins directly but it is better to stick to the
    # convention if possible
    #-----------------------------------------------------------------------------------------
    def _init_gpio_pins(self):
        self.gpio.available_pins = [496, 497, 498, 499, 500, 501, 502, 503]
        self.pins.append(self.gpio.alloc_pin(496, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(497, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(498, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(499, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(500, GPIO.OUTPUT))
        self.pins.append(self.gpio.alloc_pin(501, GPIO.OUTPUT))
        self.pins.append(self.gpio.alloc_pin(502, GPIO.OUTPUT))
        self.pins.append(self.gpio.alloc_pin(503, GPIO.OUTPUT))

    # enable/disable waking thread on RFID read
    def wakeOnRFID(self, enabled):
        self.logger.debug('wakeOnRFID enabled=%s' % enabled)
        if enabled:
            self.app.validScan.connect(self.__slotValidScan)
            self.app.invalidScan.connect(self.__slotInvalidScan)
        else:
            self.app.validScan.disconnect(self.__slotValidScan)
            self.app.invalidScan.disconnect(self.__slotInvalidScan)

    # slot to handle a valid RFID scan (whether that member is allowed or not)
    def __slotValidScan(self, record):
        self.logger.debug('valid scan: %s (%s)' % (record.name, record.allowed))

        self.mutex.lock()
        if record.valid and record.allowed:
            self.wakereason = self.REASON_VALID_SCAN
        else:
            self.wakereason = self.REASON_INVALID_SCAN

        self.mutex.unlock()
        self.cond.wakeAll()

    # slot to handle an invalid RFID scan (unknown tag, bad tag, error, etc.)
    def __slotInvalidScan(self, reason):
        self.logger.debug('invalid scan: %s' % reason)

        self.mutex.lock()
        self.wakereason = self.REASON_INVALID_SCAN
        self.mutex.unlock()
        self.cond.wakeAll()

    # enable/disable waking the thread on the timer
    def wakeOnTimer(self, enabled, interval=1000, singleShot=False):
        self.logger.debug('wakeOnTimer enabled=%s interval=%d singleShot=%s' % (enabled, interval, singleShot))
        if enabled:
            self.timerStop.emit()
            self.timer.setSingleShot(singleShot)
            self.timerStart.emit(interval)
        else:
            self.timerStop.emit()

    # slot to handle timer tick
    def __timerTick(self):
        self.mutex.lock()
        self.wakereason = self.REASON_TIMER
        self.mutex.unlock()
        self.cond.wakeAll()
