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

from PersonalityStateMachine import PersonalityStateMachine
from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty, QVariant
from PyQt5.QtQml import qmlRegisterType
from Logger import Logger
from RFID import RFID
from MemberRecord import MemberRecord
import copy
import simplejson as json

import QtGPIO as GPIO
import QtSimGPIO as SimGPIO

class PersonalityBase(PersonalityStateMachine):
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
    GPIO_PIN_LED1 = 508
    GPIO_PIN_LED2 = 509

    pinToName = {GPIO_PIN_SHUTDOWN : 'SHUTDOWN',
                 GPIO_PIN_POWER_PRESENT : 'POWER_PRESENT',
                 GPIO_PIN_CHARGE_STATE : 'CHARGE_STATE',
                 GPIO_PIN_LED1 : 'LED1',
                 GPIO_PIN_LED2 : 'LED2',
                 GPIO_PIN_IN0 : 'IN0',
                 GPIO_PIN_IN1 : 'IN1',
                 GPIO_PIN_IN2 : 'IN2',
                 GPIO_PIN_IN3 : 'IN3',
                 GPIO_PIN_OUT0 : 'OUT0',
                 GPIO_PIN_OUT1 : 'OUT1',
                 GPIO_PIN_OUT2 : 'OUT2',
                 GPIO_PIN_OUT3 : 'OUT3'}

    nameToPin = {'SHUTDOWN' : GPIO_PIN_SHUTDOWN,
                 'POWER_PRESENT' : GPIO_PIN_POWER_PRESENT,
                 'CHARGE_STATE' : GPIO_PIN_CHARGE_STATE,
                 'LED1' : GPIO_PIN_LED1,
                 'LED2' : GPIO_PIN_LED2,
                 'IN0' : GPIO_PIN_IN0,
                 'IN1' : GPIO_PIN_IN1,
                 'IN2' : GPIO_PIN_IN2,
                 'IN3' : GPIO_PIN_IN3,
                 'OUT0' : GPIO_PIN_OUT0,
                 'OUT1' : GPIO_PIN_OUT1,
                 'OUT2' : GPIO_PIN_OUT2,
                 'OUT3' : GPIO_PIN_OUT3}

    validScan = pyqtSignal(MemberRecord, name='validScan', arguments=['record'])
    invalidScan = pyqtSignal(str, name='invalidScan', arguments=['reason'])

    lockReasonChanged = pyqtSignal()

    simGPIOChanged = pyqtSignal()
    simGPIOPinChanged = pyqtSignal(str, bool, arguments=['pinName', 'value'])

    @pyqtProperty(str, notify=lockReasonChanged)
    def lockReason(self):
        self.mutex.lock()
        s = self._lockReason
        self.mutex.unlock()
        return s

    @pyqtProperty(bool, notify=simGPIOChanged)
    def simGPIO(self):
        return self._simGPIO


    def __init__(self, loglevel='WARNING', app=None):

        self.logger = Logger(name='ratt.personality')
        self.logger.setLogLevelStr(loglevel)

        PersonalityStateMachine.__init__(self, logger=self.logger)

        self.logger.info('Personality is ' + self.descr())
        self.debug = self.logger.isDebug()

        if app is None:
            self.logger.error('must set app to QQmlApplicationEngine object')
            exit(-1)

        self.app = app

        # holds the currently active member record after RFID scan and ACL lookup
        self.activeMemberRecord = MemberRecord()

        # expose the active member record to QML
        self.app.rootContext().setContextProperty("activeMemberRecord", self.activeMemberRecord)
        qmlRegisterType(MemberRecord, 'RATT', 1, 0, 'MemberRecord')

        self.app.rfid.tagScan.connect(self.__slotTagScan)

        self.telemetryEvent.connect(self.app.mqtt.slotPublishSubtopic)

        self._rfidErrorReason = ''
        self._lockReason = ''

        self.app.mqtt.broadcastEvent.connect(self.__slotBroadcastMQTTEvent)
        self.app.mqtt.targetedEvent.connect(self.__slotTargetedMQTTEvent)
        self.app.mqtt.brokerConnectionEvent.connect(self.__slotBrokerConnectionMQTTEvent)

        self.stateChanged.connect(self.__slotStateChanged)

        self.__init_gpio()


    def descr(self):
        return self.PERSONALITY_DESCRIPTION


    # de-initialize the personality
    def deinit(self):
        self.logger.info('Personality deinit')
        self.__deinit_gpio_pins()

    # gpio initialization
    def __init_gpio(self):
        self._simGPIO = False

        if not self.app.config.value('GPIO.Simulated'):
            self.gpio = GPIO.Controller()
        else:
            self.logger.warning('Using simulated GPIO')
            self.gpio = SimGPIO.Controller()
            self._simGPIO = True

        self.pins_in = []
        self.pins_out = []
        self._init_gpio_pins()

        if self._simGPIO:
            # simulated GPIO output pins connect to a handler to generate
            # a signal with a named pin and new value
            #
            # it may seem a bit backwards to be listening to changes on
            # output pins but remember, this is for the diagnostics display
            # for development, in lieu of actually outputting to a real pin
            self.pins_out[0].pinChanged.connect(self.slotSimGPIOPinChanged)
            self.pins_out[1].pinChanged.connect(self.slotSimGPIOPinChanged)
            self.pins_out[2].pinChanged.connect(self.slotSimGPIOPinChanged)
            self.pins_out[3].pinChanged.connect(self.slotSimGPIOPinChanged)

            self.pin_led1.pinChanged.connect(self.slotSimGPIOPinChanged)
            self.pin_led2.pinChanged.connect(self.slotSimGPIOPinChanged)
            self.pin_shutdown.pinChanged.connect(self.slotSimGPIOPinChanged)

    @pyqtSlot()
    def slotForceSimGPIOUpdate(self):
        if self._simGPIO:
            self.simGPIOPinChanged.emit(self.pinToName[self.pins_out[0].number], self.pins_out[0].value)
            self.simGPIOPinChanged.emit(self.pinToName[self.pins_out[1].number], self.pins_out[1].value)
            self.simGPIOPinChanged.emit(self.pinToName[self.pins_out[2].number], self.pins_out[2].value)
            self.simGPIOPinChanged.emit(self.pinToName[self.pins_out[3].number], self.pins_out[3].value)

            self.simGPIOPinChanged.emit(self.pinToName[self.pin_led1.number], self.pin_led1.value)
            self.simGPIOPinChanged.emit(self.pinToName[self.pin_led2.number], self.pin_led2.value)
            self.simGPIOPinChanged.emit(self.pinToName[self.pin_shutdown.number], self.pin_shutdown.value)


    # this slot handles pin changes for simulated GPIO and regenerates
    # a new signal with a named I/O pin for the Diags QML
    @pyqtSlot(int, bool)
    def slotSimGPIOPinChanged(self, pin, value):
        if self._simGPIO and pin in self.pinToName:
            pinName = self.pinToName[pin]
            self.simGPIOPinChanged.emit(pinName, value)

    # the Diags QML calls this slot to set a simulated GPIO pin value
    # again, this may seem backwards since this is used to set input pin values
    # in the QML, but remember, this is for simulation to make onscreen controls
    # appear to be actual GPIO inputs
    @pyqtSlot(str, bool)
    def slotSimGPIOChangePin(self, pinName, value):
        if self._simGPIO and pinName in self.nameToPinObject:
            self.nameToPinObject[pinName].set(value)

    # callback for when one of the application GPIO input pins has changed state
    # it wakes the thread with REASON_GPIO
    def __pinchanged(self, num, state):
        self.mutex.lock()
        self.wakereason = self.REASON_GPIO
        self.mutex.unlock()
        self.cond.wakeAll()

    # callback when any of the GPIOs which monitor the power and charge status changes state
    # it wakes the thread with REASON_POWER_LOST or REASON_POWER_RESTORED depending on the event
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
                                    self.GPIO_PIN_LED1,
                                    self.GPIO_PIN_LED2,
                                    self.GPIO_PIN_IN0,
                                    self.GPIO_PIN_IN1,
                                    self.GPIO_PIN_IN2,
                                    self.GPIO_PIN_IN3,
                                    self.GPIO_PIN_OUT0,
                                    self.GPIO_PIN_OUT1,
                                    self.GPIO_PIN_OUT2,
                                    self.GPIO_PIN_OUT3]

        self.pins_in.append(self.gpio.alloc_pin(self.GPIO_PIN_IN0, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins_in.append(self.gpio.alloc_pin(self.GPIO_PIN_IN1, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins_in.append(self.gpio.alloc_pin(self.GPIO_PIN_IN2, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))
        self.pins_in.append(self.gpio.alloc_pin(self.GPIO_PIN_IN3, GPIO.INPUT, self.__pinchanged, GPIO.BOTH))

        self.pins_out.append(self.gpio.alloc_pin(self.GPIO_PIN_OUT0, GPIO.OUTPUT))
        self.pins_out.append(self.gpio.alloc_pin(self.GPIO_PIN_OUT1, GPIO.OUTPUT))
        self.pins_out.append(self.gpio.alloc_pin(self.GPIO_PIN_OUT2, GPIO.OUTPUT))
        self.pins_out.append(self.gpio.alloc_pin(self.GPIO_PIN_OUT3, GPIO.OUTPUT))

        self.pin_led1 = self.gpio.alloc_pin(self.GPIO_PIN_LED1, GPIO.OUTPUT, active_low=1)
        self.pin_led2 = self.gpio.alloc_pin(self.GPIO_PIN_LED2, GPIO.OUTPUT, active_low=1)

        self.pin_shutdown = self.gpio.alloc_pin(self.GPIO_PIN_SHUTDOWN, GPIO.OUTPUT)
        self.pin_shutdown.set(GPIO.HIGH)

        self.pin_powerpresent = self.gpio.alloc_pin(self.GPIO_PIN_POWER_PRESENT, GPIO.INPUT, self.__power_event, GPIO.BOTH)
        self.pin_charge_state = self.gpio.alloc_pin(self.GPIO_PIN_CHARGE_STATE, GPIO.INPUT)

        self.nameToPinObject = {'SHUTDOWN' : self.pin_shutdown,
                                'POWER_PRESENT' : self.pin_powerpresent,
                                'CHARGE_STATE' : self.pin_charge_state,
                                'LED1' : self.pin_led1,
                                'LED2' : self.pin_led2,
                                'IN0' : self.pins_in[0],
                                'IN1' : self.pins_in[1],
                                'IN2' : self.pins_in[2],
                                'IN3' : self.pins_in[3],
                                'OUT0' : self.pins_out[0],
                                'OUT1' : self.pins_out[1],
                                'OUT2' : self.pins_out[2],
                                'OUT3' : self.pins_out[3]}


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

        self._rfidErrorReason = ''

        self.mutex.unlock()
        self.cond.wakeAll()

    # slot to handle an invalid RFID scan (unknown tag, bad tag, error, etc.)
    def __slotInvalidScan(self, reason):
        self.logger.debug('invalid scan: %s' % reason)

        empty = MemberRecord()

        self.activeMemberRecord.copy(source=empty)

        self.mutex.lock()
        self.wakereason = self.REASON_RFID_ERROR
        self._rfidErrorReason = reason
        self.mutex.unlock()
        self.cond.wakeAll()

    # MQTT targeted event
    @pyqtSlot(str, str)
    def __slotTargetedMQTTEvent(self, subtopic, message):
        tsplit = subtopic.split('/')

        if len(tsplit) >= 2 and tsplit[0] == 'personality':
            cmd = tsplit[1]

            if cmd == 'lock':
                self.mutex.lock()
                self.wakereason = self.REASON_LOCK_OUT
                self.mutex.unlock()
                self.cond.wakeAll()

                if len(message):
                    self._lockReason = message
                else:
                    self._lockReason = '(no reason given)'
                self.lockReasonChanged.emit()

            elif cmd == 'unlock':
                self.mutex.lock()
                self.wakereason = self.REASON_LOCK_OUT_CANCELED
                self.mutex.unlock()
                self.cond.wakeAll()

    # MQTT broadcast event
    @pyqtSlot(str, str)
    def __slotBroadcastMQTTEvent(self, subtopic, message):
        self.logger.debug('MQTT broadcast ' + subtopic + ' -> ' + message)

    # MQTT broker connection EnvironmentError
    @pyqtSlot(bool)
    def __slotBrokerConnectionMQTTEvent(self, connected):
        self.logger.info('MQTT broker connection event, connection is ' + str(connected))
        if connected:
            # send out the current state upon broker (re-)connection
            self.mutex.lock()
            state = self.state
            phase = self.phaseName(self.statePhase)
            self.mutex.unlock()
            self.__slotStateChanged(state, phase)

    @pyqtSlot(str, str)
    def __slotStateChanged(self, state, phase):
        self.telemetryEvent.emit('personality/state', json.dumps({ 'state': state, 'phase': phase}))
        self.app.rfid.serialOut('%s.%s\n' % (state, phase))
