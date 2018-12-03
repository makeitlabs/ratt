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
import QtGPIO as GPIO
import copy

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

    validScan = pyqtSignal(MemberRecord, name='validScan', arguments=['record'])
    invalidScan = pyqtSignal(str, name='invalidScan', arguments=['reason'])

    telemetryEvent = pyqtSignal(str, str, name='telemetryEvent', arguments=['subtopic', 'message'])
    lockReasonChanged = pyqtSignal()

    @pyqtProperty(str, notify=lockReasonChanged)
    def lockReason(self):
        self.mutex.lock()
        s = self._lockReason
        self.mutex.unlock()
        return s

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
        self.gpio = GPIO.Controller()
        self.pins_in = []
        self.pins_out = []
        self._init_gpio_pins()

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
            self.app.mqtt.publish(subtopic='personality/state', msg=state + '.' + phase)

    @pyqtSlot(str, str)
    def __slotStateChanged(self, state, phase):
        self.app.mqtt.publish(subtopic='personality/state', msg=state + '.' + phase)
