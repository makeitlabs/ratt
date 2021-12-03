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

from PyQt5.QtCore import QThread, QMutex, QWaitCondition, QTimer
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty, QVariant
from Logger import Logger
import json

class PersonalityStateMachine(QThread):
    # state phases
    PHASE_ENTER = 0
    PHASE_ACTIVE = 1
    PHASE_EXIT = 100

    phaseLookup = { PHASE_ENTER : 'ENTER', PHASE_ACTIVE : 'ACTIVE', PHASE_EXIT : 'EXIT' }

    # thread wake reasons
    REASON_NONE = 0
    REASON_TIMEOUT = 1
    REASON_TIMER = 2
    REASON_GPIO = 3
    REASON_RFID_ALLOWED = 4
    REASON_RFID_DENIED = 5
    REASON_RFID_ERROR = 6
    REASON_UI = 7
    REASON_MQTT = 10
    REASON_LOCK_OUT = 20
    REASON_LOCK_OUT_CANCELED = 21
    REASON_POWER_LOST = 100
    REASON_POWER_RESTORED = 101
    REASON_BATTERY_CHARGING = 102
    REASON_BATTERY_CHARGED = 103

    reasonLookup = { REASON_NONE : 'NONE', REASON_TIMEOUT : 'TIMEOUT', REASON_TIMER : 'TIMER',
                     REASON_GPIO : 'GPIO' ,
                     REASON_RFID_ALLOWED : 'RFID_ALLOWED', REASON_RFID_DENIED : 'RFID_DENIED',
                     REASON_RFID_ERROR : 'RFID_ERROR',
                     REASON_UI : 'UI',
                     REASON_MQTT : 'MQTT',
                     REASON_LOCK_OUT : 'LOCK_OUT', REASON_LOCK_OUT_CANCELED : 'LOCK_OUT_CANCELED',
                     REASON_POWER_LOST : 'POWER_LOST', REASON_POWER_RESTORED : 'POWER_RESTORED',
                     REASON_BATTERY_CHARGING : 'BATTERY_CHARGING', REASON_BATTERY_CHARGED : 'BATTERY_CHARGED'}

    # pre-defined states that are present in all implementations
    STATE_POWER_LOSS = 'PowerLoss'
    STATE_SHUT_DOWN = 'ShutDown'
    STATE_LOCK_OUT = 'LockOut'

    # this list should be populated by the inheriting class with the valid states that allow immediate lockout
    # at a minimum it's usually the idle state .. it's left empty here
    validLockoutStates = []

    stateChanged = pyqtSignal(str, str, name='stateChanged', arguments=['state', 'phase'])
    pinChanged = pyqtSignal(int, int, name='pinChanged', arguments=['pin', 'state'])

    timerStart = pyqtSignal(int, name='timerStart', arguments=['msec'])
    timerStop = pyqtSignal()

    telemetryEvent = pyqtSignal(str, str, name='telemetryEvent', arguments=['subtopic', 'message'])

    @pyqtProperty(str, notify=stateChanged)
    def currentState(self):
        return self.stateName()

    def __init__(self, logger=None):
        QThread.__init__(self)

        self.cond = QWaitCondition()
        self.mutex = QMutex()

        if logger is None:
            exit(-1)

        self.logger = logger

        self.wakereason = self.REASON_NONE
        self.uievent = ''

        self.state = None
        self.statePhase = None

        self.timer = QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.__timerTick)

        self.timerStart.connect(self.timer.start)
        self.timerStop.connect(self.timer.stop)
        self.wasLockedOut = False

        self.lockoutPending = False
        self.quit = False

    # returns the specified wake reason as a human-friendly string, or will return the current wakereason string
    def reasonName(self, reason = None):
        if reason == None:
            reason = self.wakereason

        return self.reasonLookup[reason]

    # starts the thread running if it's not already
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

            if self.wakereason is self.REASON_UI:
                self.logger.debug('%s woke up because %s:%s' % (self.stateName(), self.reasonName(), self.uievent))
            else:
                self.logger.debug('%s woke up because %s' % (self.stateName(), self.reasonName()))

            if self.wakereason is self.REASON_POWER_LOST:
                self.logger.info('Power loss detected, going to shutdown state.')
                self.exitAndGoto(self.STATE_POWER_LOSS)

            if self.wakereason is self.REASON_LOCK_OUT:
                self.lockoutPending = True
                self.telemetryEvent.emit('personality/lockout', json.dumps({'state': 'pending', 'reason': self._lockReason}))

            if self.wakereason is self.REASON_LOCK_OUT_CANCELED:
                if self.lockoutPending or self.state == self.STATE_LOCK_OUT:
                    self.telemetryEvent.emit('personality/lockout', json.dumps({'state': 'unlocked'}))

                self.lockoutPending = False
                self.wasLockedOut = False
                if self.state == self.STATE_LOCK_OUT:
                    self.exitAndGoto(self.STATE_INIT)

            if self.lockoutPending and self.state in self.validLockoutStates:
                self.telemetryEvent.emit('personality/lockout', json.dumps({'state': 'locked', 'reason': self._lockReason}))
                self.lockoutPending = False;
                self.exitAndGoto(self.STATE_LOCK_OUT)

            # run the state machine until a False is returned (meaning go back to waiting)
            again = True
            while again:
                curStateFunc = self.states[self.state]
                again = curStateFunc()
                self.wakereason = self.REASON_NONE

            self.mutex.unlock()

    # returns specified phase as a human-friendly string
    def phaseName(self, phase):
        if phase in self.phaseLookup:
            return self.phaseLookup[phase]
        elif phase >= self.PHASE_ACTIVE and phase < self.PHASE_EXIT:
            return '%s.%d' % (self.phaseLookup[self.PHASE_ACTIVE], phase - self.PHASE_ACTIVE)


    # returns specified state/phase as a human-friendly string
    # if state/phase not specified, will return the current state/phase string
    def stateName(self, state = None, phase = None):
        if state == None or phase == None:
            state = self.state
            phase = self.statePhase

        return '%s.%s' % (state, self.phaseName(phase))


    # execute a state change to the specified state and phase
    # emits the stateChanged signal upon change
    def setState(self, state, phase):
        if state in self.states:
            if state != self.state or phase != self.statePhase:
                self.logger.debug('setState %s ==> %s' % (self.stateName(self.state, self.statePhase), self.stateName(state, phase)))
                self.state = state
                self.statePhase = phase

                self.stateChanged.emit(self.state, self.phaseName(self.statePhase))
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
        self.stateChanged.emit(self.state, self.phaseName(self.statePhase))
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

    # slot to handle event from UI
    @pyqtSlot(str)
    def slotUIEvent(self, evt):
        self.mutex.lock()
        self.wakereason = self.REASON_UI
        self.uievent = evt
        self.mutex.unlock()
        self.cond.wakeAll()
