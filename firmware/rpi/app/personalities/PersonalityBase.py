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
import qgpio as GPIO

class PersonalityBase(QThread):
    STATE_UNINITIALIZED = 'Uninitialized'
    STATE_INIT = 'Init'
    STATE_IDLE = 'Idle'
    STATE_LOCKOUT_CHECK = 'LockoutCheck'
    STATE_RFID_LOOKUP = 'RFIDLookup'
    STATE_ACCESS_DENIED = 'AccessDenied'
    STATE_ACCESS_ALLOWED = 'AccessAllowed'
    STATE_SAFETY_CHECK = 'SafetyCheck'
    STATE_SAFETY_CHECK_PASSED = 'SafetyCheckPassed'
    STATE_SAFETY_CHECK_FAILED = 'SafetyCheckFailed'
    STATE_TOOL_ENABLED_INACTIVE = 'ToolEnabledInactive'
    STATE_TOOL_ENABLED_ACTIVE = 'ToolEnabledActive'
    STATE_TOOL_TIMEOUT_WARNING = 'ToolTimeoutWarning'
    STATE_TOOL_TIMEOUT = 'ToolTimeout'
    STATE_TOOL_DISABLED = 'ToolDisabled'

    PHASE_ENTER = 0
    PHASE_ACTIVE = 1
    PHASE_EXIT = 2

    phaseLookup = { PHASE_ENTER : 'ENTER', PHASE_ACTIVE : 'ACTIVE', PHASE_EXIT : 'EXIT' }

    REASON_NONE = 0
    REASON_TIMEOUT = 1
    REASON_GPIO = 2
    REASON_VALID_SCAN = 3
    REASON_INVALID_SCAN = 4

    reasonLookup = { REASON_NONE : 'NONE', REASON_TIMEOUT : 'TIMEOUT', REASON_GPIO : 'GPIO' ,
                     REASON_VALID_SCAN : 'VALID_SCAN', REASON_INVALID_SCAN : 'INVALID_SCAN'}

    stateChanged = pyqtSignal(str, int, name='stateChanged', arguments=['state', 'phase'])
    pinChanged = pyqtSignal(int, int, name='pinChanged', arguments=['pin', 'state'])

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

        self.states = {self.STATE_UNINITIALIZED : self._stateUninitialized,
                       self.STATE_INIT : self._stateInit,
                       self.STATE_IDLE : self._stateIdle,
                       self.STATE_LOCKOUT_CHECK : self._stateLockoutCheck,
                       self.STATE_RFID_LOOKUP : self._stateRFIDLookup,
                       self.STATE_ACCESS_DENIED : self._stateAccessDenied,
                       self.STATE_ACCESS_ALLOWED : self._stateAccessAllowed,
                       self.STATE_SAFETY_CHECK : self._stateSafetyCheck,
                       self.STATE_SAFETY_CHECK_PASSED : self._stateSafetyCheckPassed,
                       self.STATE_SAFETY_CHECK_FAILED : self._stateSafetyCheckFailed,
                       self.STATE_TOOL_ENABLED_INACTIVE : self._stateToolEnabledInactive,
                       self.STATE_TOOL_ENABLED_ACTIVE : self._stateToolEnabledActive,
                       self.STATE_TOOL_TIMEOUT_WARNING : self._stateToolTimeoutWarning,
                       self.STATE_TOOL_TIMEOUT : self._stateToolTimeout,
                       self.STATE_TOOL_DISABLED : self._stateToolDisabled
                       }

        self.state = self.STATE_UNINITIALIZED
        self.statePhase = self.PHASE_ACTIVE

        self.wakereason = self.REASON_NONE

        self.gpio = GPIO.Controller()

        self.gpio.available_pins = [496, 497, 498, 499, 500, 501, 502, 503]

        self.pins = []

        self.pins.append(self.gpio.alloc_pin(496, GPIO.INPUT, self.pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(497, GPIO.INPUT, self.pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(498, GPIO.INPUT, self.pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(499, GPIO.INPUT, self.pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(500, GPIO.OUTPUT))
        self.pins.append(self.gpio.alloc_pin(501, GPIO.OUTPUT))
        self.pins.append(self.gpio.alloc_pin(502, GPIO.OUTPUT))
        self.pins.append(self.gpio.alloc_pin(503, GPIO.OUTPUT))

    def descr(self):
        return 'Personality base class.'

    def pinchanged(self, num, state):
        self.logger.debug('gpio pin changed %d %d' % (num, state))
        self.mutex.lock()
        self.wakereason = self.REASON_GPIO
        self.mutex.unlock()
        self.cond.wakeAll()


    def execute(self):
        if not self.isRunning():
            self.start();

    def run(self):
        self.logger.debug('thread run')

        self.setState(self.STATE_INIT, 0)

        # initialize
        again = True
        while again:
            curStateFunc = self.states[self.state]
            again = curStateFunc()

        while not self.quit:
            self.mutex.lock()
            self.cond.wait(self.mutex)
            self.logger.debug('%s woke up because %s' % (self.stateName(), self.reasonName()))

            again = True
            while again:
                curStateFunc = self.states[self.state]
                again = curStateFunc()
                self.wakereason = self.REASON_NONE

            self.mutex.unlock()

    def stateName(self, state = None, phase = None):
        if state == None or phase == None:
            state = self.state
            phase = self.statePhase

        return '%s.%s' % (state, self.phaseLookup[phase])

    def reasonName(self, reason = None):
        if reason == None:
            reason = self.wakereason

        return self.reasonLookup[reason]

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


    '''
    ---------------------------------------------------------------------------------------------------------------
    '''

    def _stateUninitialized(self):
        pass

    def _stateInit(self):
        self.logger.debug('initialize')
        self.pins[4].reset()
        self.pins[5].reset()
        self.pins[6].reset()
        self.pins[7].reset()
        return self.setState(self.STATE_IDLE, self.PHASE_ENTER)

    def _validScanHandler(self, record):
        self.logger.debug('scanned rfid')

        self.mutex.lock()
        if record.valid and record.allowed:
            self.wakereason = self.REASON_VALID_SCAN
        else:
            self.wakereason = self.REASON_INVALID_SCAN

        self.mutex.unlock()
        self.cond.wakeAll()

    def _invalidScanHandler(self, reason):
        self.logger.debug('invalid scan: %s' % reason)

        self.mutex.lock()
        self.wakereason = self.REASON_INVALID_SCAN
        self.mutex.unlock()
        self.cond.wakeAll()

    def _stateIdle(self):
        if self.statePhase is self.PHASE_ENTER:
            self.logger.debug('idle enter')
            self.app.validScan.connect(self._validScanHandler)
            self.app.invalidScan.connect(self._invalidScanHandler)
            self.pins[4].set()
            return self.setState(self.STATE_IDLE, self.PHASE_ACTIVE)

        elif self.statePhase is self.PHASE_ACTIVE:
            self.logger.debug('idle')

            if self.wakereason == self.REASON_VALID_SCAN:
                return self.exitAndGoto(self.STATE_ACCESS_ALLOWED)

            if self.wakereason == self.REASON_INVALID_SCAN:
                return self.exitAndGoto(self.STATE_ACCESS_DENIED)

            # otherwise thread goes back to waiting
            return False

        elif self.statePhase is self.PHASE_EXIT:
            self.logger.debug('idle exit')
            self.app.validScan.disconnect(self._validScanHandler)
            self.app.invalidScan.disconnect(self._invalidScanHandler)

            return self.goNextState()


    def _stateLockoutCheck(self):
        pass

    def _stateRFIDLookup(self):
        pass

    def _stateAccessDenied(self):
        return self.setState(self.STATE_IDLE, self.PHASE_ENTER)

    def _stateAccessAllowed(self):
        if self.statePhase is self.PHASE_ENTER:
            self.pins[5].set()
            return self.setState(self.STATE_ACCESS_ALLOWED, self.PHASE_ACTIVE)

        elif self.statePhase is self.PHASE_ACTIVE:
            self.logger.debug('access allowed')

            if self.wakereason == self.REASON_GPIO and self.pins[0].read() == 0:
                return self.exitAndGoto(self.STATE_IDLE)

            return False
        elif self.statePhase is self.PHASE_EXIT:
            self.pins[5].reset()
            return self.goNextState()
        pass

    def _stateSafetyCheck(self):
        pass

    def _stateSafetyCheckPassed(self):
        pass

    def _stateSafetyCheckFailed(self):
        pass

    def _stateToolEnabledActive(self):
        pass

    def _stateToolEnabledInactive(self):
        pass

    def _stateToolTimeoutWarning(self):
        pass

    def _stateToolTimeout(self):
        pass

    def _stateToolDisabled(self):
        pass
