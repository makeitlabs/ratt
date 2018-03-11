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
from PyQt5.QtQml import qmlRegisterType
from Logger import Logger
from RFID import RFID
from MemberRecord import MemberRecord
import QtGPIO as GPIO
import copy

class PersonalityBase(QThread):
    PERSONALITY_DESCRIPTION = 'Base'

    # GPIO pin assignments
    GPIO_PIN_SHUTDOWN = 27
    GPIO_PIN_POWER_PRESENT = 26
    GPIO_PIN_CHARGE_STATE = 12
    GPIO_PIN_IN0 = 496
    GPIO_PIN_IN1 = 497
    GPIO_PIN_IN2 = 498
    GPIO_PIN_IN3 = 499
    GPIO_PIN_OUT0 = 500
    GPIO_PIN_OUT1 = 501
    GPIO_PIN_OUT2 = 502
    GPIO_PIN_OUT3 = 503

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
    REASON_POWER_LOST = 100
    REASON_POWER_RESTORED = 101
    REASON_BATTERY_CHARGING = 102
    REASON_BATTERY_CHARGED = 103

    STATE_POWER_LOSS = 'PowerLoss'
    STATE_SHUT_DOWN = 'ShutDown'

    reasonLookup = { REASON_NONE : 'NONE', REASON_TIMEOUT : 'TIMEOUT', REASON_TIMER : 'TIMER',
                     REASON_GPIO : 'GPIO' ,
                     REASON_RFID_ALLOWED : 'RFID_ALLOWED', REASON_RFID_DENIED : 'RFID_DENIED',
                     REASON_RFID_ERROR : 'RFID_ERROR',
                     REASON_UI : 'UI',
                     REASON_POWER_LOST : 'POWER_LOST', REASON_POWER_RESTORED : 'POWER_RESTORED',
                     REASON_BATTERY_CHARGING : 'BATTERY_CHARGING', REASON_BATTERY_CHARGED : 'BATTERY_CHARGED'}




    stateChanged = pyqtSignal(str, str, name='stateChanged', arguments=['state', 'phase'])
    pinChanged = pyqtSignal(int, int, name='pinChanged', arguments=['pin', 'state'])

    timerStart = pyqtSignal(int, name='timerStart', arguments=['msec'])
    timerStop = pyqtSignal()

    validScan = pyqtSignal(MemberRecord, name='validScan', arguments=['record'])
    invalidScan = pyqtSignal(str, name='invalidScan', arguments=['reason'])

    telemetryEvent = pyqtSignal(str, str, name='telemetryEvent', arguments=['event_type', 'message'])

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
        self.uievent = ''

        self.timer = QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.__timerTick)

        self.timerStart.connect(self.timer.start)
        self.timerStop.connect(self.timer.stop)

        # holds the currently active member record after RFID scan and ACL lookup
        self.activeMemberRecord = MemberRecord()

        # expose the active member record to QML
        self.app.rootContext().setContextProperty("activeMemberRecord", self.activeMemberRecord)
        qmlRegisterType(MemberRecord, 'RATT', 1, 0, 'MemberRecord')

        self.app.rfid.tagScan.connect(self.__slotTagScan)

        self.telemetryEvent.connect(self.app.telemetry.logEvent)

        self.__init_gpio()


    def descr(self):
        return self.PERSONALITY_DESCRIPTION

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

            # run the state machine until a False is returned (meaning go back to waiting)
            again = True
            while again:
                curStateFunc = self.states[self.state]
                again = curStateFunc()
                self.wakereason = self.REASON_NONE

            self.mutex.unlock()


    def deinit(self):
        self.logger.info('Personality deinit')
        self.__deinit_gpio_pins()


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

    # this is a callback when any of the GPIOs which monitor the power and charge status changes state
    def __power_event(self, num, state):
        reason = self.REASON_NONE
        if not state:
            reason = self.REASON_POWER_LOST
        else:
            reason = self.REASON_POWER_RESTORED

        self.mutex.lock()
        self.wakereason = reason
        self.mutex.unlock()
        self.cond.wakeAll()

    def __charge_event(self, num, state):
        if not state:
            reason = self.REASON_BATTERY_CHARGED
        else:
            reason = self.REASON_BATTERY_CHARGING

        self.mutex.lock()
        self.wakereason = reason
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
        self.gpio.available_pins = [self.GPIO_PIN_SHUTDOWN,
                                    self.GPIO_PIN_POWER_PRESENT,
                                    self.GPIO_PIN_CHARGE_STATE,
                                    self.GPIO_PIN_IN0,
                                    self.GPIO_PIN_IN1,
                                    self.GPIO_PIN_IN2,
                                    self.GPIO_PIN_IN3,
                                    self.GPIO_PIN_OUT0,
                                    self.GPIO_PIN_OUT1,
                                    self.GPIO_PIN_OUT2,
                                    self.GPIO_PIN_OUT3]

        self.pins.append(self.gpio.alloc_pin(self.GPIO_PIN_IN0, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(self.GPIO_PIN_IN1, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(self.GPIO_PIN_IN2, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(self.GPIO_PIN_IN3, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins.append(self.gpio.alloc_pin(self.GPIO_PIN_OUT0, GPIO.OUTPUT))
        self.pins.append(self.gpio.alloc_pin(self.GPIO_PIN_OUT1, GPIO.OUTPUT))
        self.pins.append(self.gpio.alloc_pin(self.GPIO_PIN_OUT2, GPIO.OUTPUT))
        self.pins.append(self.gpio.alloc_pin(self.GPIO_PIN_OUT3, GPIO.OUTPUT))

        self.pin_shutdown = self.gpio.alloc_pin(self.GPIO_PIN_SHUTDOWN, GPIO.OUTPUT)
        self.pin_shutdown.set(GPIO.HIGH)

        self.pin_powerpresent = self.gpio.alloc_pin(self.GPIO_PIN_POWER_PRESENT, GPIO.INPUT, self.__power_event, GPIO.BOTH)
        self.pin_charge_state = self.gpio.alloc_pin(self.GPIO_PIN_CHARGE_STATE, GPIO.INPUT)

    # de-allocate the gpio pins, EXCEPT for the shutdown pin (because that would potentially turn RATT off)
    def __deinit_gpio_pins(self):
        for pin in self.gpio.available_pins:
            if pin != self.GPIO_PIN_SHUTDOWN:
                self.gpio.dealloc_pin(pin)

    # enable/disable waking thread on RFID read
    def wakeOnRFID(self, enabled):
        self.logger.debug('wakeOnRFID enabled=%s' % enabled)
        if enabled:
            self.validScan.connect(self.__slotValidScan)
            self.invalidScan.connect(self.__slotInvalidScan)
        else:
            self.validScan.disconnect(self.__slotValidScan)
            self.invalidScan.disconnect(self.__slotInvalidScan)


    # slot to handle a valid RFID scan (whether that member is allowed or not)
    def __slotTagScan(self, tag, hash, time, debugText):
        self.logger.debug('tag scanned tag=%d hash=%s time=%d debug=%s' % (tag, hash, time, debugText))

        result = self.app.acl.search(hash)

        if result != []:
            record = MemberRecord()
            success = record.parseRecord(result)

            if success:
                self.validScan.emit(record)
            else:
                self.invalidScan.emit('error creating MemberRecord')
                self.logger.error('error creating MemberRecord')
        else:
            self.invalidScan.emit('unknown rfid tag')
            self.logger.info('unknown rfid tag')


    # slot to handle a valid RFID scan (whether that member is allowed or not)
    def __slotValidScan(self, record):
        self.logger.debug('valid scan: %s (%s)' % (record.name, record.allowed))

        self.activeMemberRecord.copy(source=record)

        self.mutex.lock()
        if record.valid and record.allowed:
            self.wakereason = self.REASON_RFID_ALLOWED
        else:
            self.wakereason = self.REASON_RFID_DENIED

        self.mutex.unlock()
        self.cond.wakeAll()

    # slot to handle an invalid RFID scan (unknown tag, bad tag, error, etc.)
    def __slotInvalidScan(self, reason):
        self.logger.debug('invalid scan: %s' % reason)

        empty = MemberRecord()

        self.activeMemberRecord.copy(source=empty)

        self.mutex.lock()
        self.wakereason = self.REASON_RFID_ERROR
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

    @pyqtSlot(str)
    def slotUIEvent(self, evt):
        self.mutex.lock()
        self.wakereason = self.REASON_UI
        self.uievent = evt
        self.mutex.unlock()
        self.cond.wakeAll()
