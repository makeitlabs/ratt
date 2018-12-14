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

from PyQt5.QtCore import pyqtSlot, pyqtSignal, pyqtProperty, QVariant
from QtGPIO import LOW, HIGH
from PersonalityBase import PersonalityBase
import simplejson as json

class Personality(PersonalityBase):
    #############################################
    ## Tool Personality: Simple Tool
    #############################################
    PERSONALITY_DESCRIPTION = 'Simple'

    #############################################
    ## State definitions:
    ##     STATE_NAME = 'StateName'
    #############################################
    ## defined in PersonalityBase
    ## STATE_POWER_LOSS
    ## STATE_SHUT_DOWN
    ## STATE_LOCK_OUT
    STATE_UNINITIALIZED = 'Uninitialized'
    STATE_INIT = 'Init'
    STATE_IDLE = 'Idle'
    STATE_TOOL_NOT_POWERED = 'NotPowered'
    STATE_TOOL_NOT_POWERED_DENIED = 'NotPoweredDenied'
    STATE_ACCESS_DENIED = 'AccessDenied'
    STATE_ACCESS_ALLOWED = 'AccessAllowed'
    STATE_RFID_ERROR = 'RFIDError'
    STATE_SAFETY_CHECK = 'SafetyCheck'
    STATE_SAFETY_CHECK_PASSED = 'SafetyCheckPassed'
    STATE_SAFETY_CHECK_FAILED = 'SafetyCheckFailed'
    STATE_TOOL_ENABLED_INACTIVE = 'ToolEnabledInactive'
    STATE_TOOL_ENABLED_ACTIVE = 'ToolEnabledActive'
    STATE_TOOL_ENABLED_NOT_POWERED = 'ToolEnabledNotPowered'
    STATE_TOOL_TIMEOUT_WARNING = 'ToolTimeoutWarning'
    STATE_TOOL_TIMEOUT = 'ToolTimeout'
    STATE_TOOL_DISABLED = 'ToolDisabled'
    STATE_REPORT_ISSUE = 'ReportIssue'

    toolActiveFlagChanged = pyqtSignal()

    @pyqtProperty(bool, notify=toolActiveFlagChanged)
    def toolActiveFlag(self):
        return self._toolActiveFlag

    @toolActiveFlag.setter
    def toolActiveFlag(self, value):
        self._toolActiveFlag = value
        self.toolActiveFlagChanged.emit()


    def __init__(self, *args, **kwargs):
        PersonalityBase.__init__(self, *args, **kwargs)

        #############################################
        ## Map states to state handler functions
        #############################################
        self.states = {self.STATE_UNINITIALIZED : self.stateUninitialized,
                       self.STATE_INIT : self.stateInit,
                       self.STATE_IDLE : self.stateIdle,
                       self.STATE_TOOL_NOT_POWERED : self.stateToolNotPowered,
                       self.STATE_TOOL_NOT_POWERED_DENIED : self.stateToolNotPoweredDenied,
                       self.STATE_ACCESS_DENIED : self.stateAccessDenied,
                       self.STATE_ACCESS_ALLOWED : self.stateAccessAllowed,
                       self.STATE_RFID_ERROR : self.stateRFIDError,
                       self.STATE_SAFETY_CHECK : self.stateSafetyCheck,
                       self.STATE_SAFETY_CHECK_PASSED : self.stateSafetyCheckPassed,
                       self.STATE_SAFETY_CHECK_FAILED : self.stateSafetyCheckFailed,
                       self.STATE_TOOL_ENABLED_INACTIVE : self.stateToolEnabledInactive,
                       self.STATE_TOOL_ENABLED_ACTIVE : self.stateToolEnabledActive,
                       self.STATE_TOOL_TIMEOUT_WARNING : self.stateToolTimeoutWarning,
                       self.STATE_TOOL_TIMEOUT : self.stateToolTimeout,
                       self.STATE_TOOL_ENABLED_NOT_POWERED : self.stateToolEnabledNotPowered,
                       self.STATE_TOOL_DISABLED : self.stateToolDisabled,
                       self.STATE_REPORT_ISSUE : self.stateReportIssue,
                       self.STATE_POWER_LOSS : self.statePowerLoss,
                       self.STATE_SHUT_DOWN : self.stateShutDown,
                       self.STATE_LOCK_OUT : self.stateLockOut
                       }

        # allow lockout to happen immediately when idle or not powered .. otherwise lockout pends
        # until one of these states is reached, so that active use will not be disrupted
        self.validLockoutStates = [self.STATE_IDLE, self.STATE_TOOL_NOT_POWERED]

        # Set initial state and phase
        self.state = self.STATE_UNINITIALIZED
        self.statePhase = self.PHASE_ACTIVE

        self._toolActiveFlag = False

        self._performSafetyCheck = True
        self._monitorToolPower = False


    # initialize gpio pins to a safe 'off' state
    def initPins(self):
        self.pins_out[0].set(LOW)
        self.pins_out[1].set(LOW)
        self.pins_out[2].set(LOW)
        self.pins_out[3].set(LOW)
        self.pin_led1.set(LOW)
        self.pin_led2.set(LOW)

    # enable tool
    def enableTool(self):
        self.pins_out[0].set(HIGH)

    # disable tool
    def disableTool(self):
        self.pins_out[0].set(LOW)

    # returns true if the tool is currently active
    def toolActive(self):
        return (self.pins_in[0].get() == 0)

    # returns true if the tool is currently powered up
    def toolPowered(self):
        return (self.pins_in[1].get() == 0)

    #############################################
    ## STATE_UNINITIALIZED
    #############################################
    def stateUninitialized(self):
        pass

    #############################################
    ## STATE_INIT
    #############################################
    def stateInit(self):
        self.logger.debug('initialize')
        self.initPins()
        return self.goto(self.STATE_IDLE)

    #############################################
    ## STATE_IDLE
    #############################################
    def stateIdle(self):
        if self.phENTER:
            self.activeMemberRecord.clear()
            self.wakeOnRFID(True)
            self.pin_led1.set(HIGH)
            self.wakeOnTimer(enabled=True, interval=500, singleShot=True)
            return self.goActive()

        elif self.phACTIVE:

            if self._monitorToolPower and not self.toolPowered():
                return self.exitAndGoto(self.STATE_TOOL_NOT_POWERED)

            if self.wakereason == self.REASON_TIMER:
                if self.pin_led1.get() == LOW:
                    self.pin_led1.set(HIGH)
                    self.wakeOnTimer(enabled=True, interval=500, singleShot=True)
                else:
                    self.pin_led1.set(LOW)
                    self.wakeOnTimer(enabled=True, interval=1500, singleShot=True)
            elif self.wakereason == self.REASON_RFID_ALLOWED:
                return self.exitAndGoto(self.STATE_ACCESS_ALLOWED)
            elif self.wakereason == self.REASON_RFID_DENIED:
                return self.exitAndGoto(self.STATE_ACCESS_DENIED)
            elif self.wakereason == self.REASON_RFID_ERROR:
                return self.exitAndGoto(self.STATE_RFID_ERROR)
            elif self.wakereason == self.REASON_UI and self.uievent == 'ReportIssue':
                return self.exitAndGoto(self.STATE_REPORT_ISSUE)


            # otherwise thread goes back to waiting
            return False

        elif self.phEXIT:
            self.pin_led1.set(LOW)
            self.wakeOnTimer(False)
            self.wakeOnRFID(False)
            return self.goNextState()

    #############################################
    ## STATE_TOOL_NOT_POWERED
    #############################################
    def stateToolNotPowered(self):
        if self.phENTER:
            self.telemetryEvent.emit('personality/power', json.dumps({'powered': False}))
            self.pin_led1.set(HIGH)
            self.wakeOnRFID(True)
            self.wakeOnTimer(enabled=True, interval=1500, singleShot=True)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_TIMER:
                if self.pin_led1.get() == LOW:
                    self.pin_led1.set(HIGH)
                    self.wakeOnTimer(enabled=True, interval=1500, singleShot=True)
                else:
                    self.pin_led1.set(LOW)
                    self.wakeOnTimer(enabled=True, interval=2500, singleShot=True)

            elif (self.wakereason == self.REASON_RFID_ALLOWED):
                return self.exitAndGoto(self.STATE_TOOL_NOT_POWERED_DENIED)
            elif self.wakereason == self.REASON_RFID_DENIED:
                return self.exitAndGoto(self.STATE_TOOL_NOT_POWERED_DENIED)
            elif self.wakereason == self.REASON_RFID_ERROR:
                return self.exitAndGoto(self.STATE_TOOL_NOT_POWERED_DENIED)

            elif self.wakereason == self.REASON_UI and self.uievent == 'ReportIssue':
                return self.exitAndGoto(self.STATE_REPORT_ISSUE)

            if self.toolPowered():
                self.telemetryEvent.emit('personality/power', json.dumps({'powered': True}))
                return self.exitAndGoto(self.STATE_IDLE)

            # otherwise thread goes back to waiting
            return False

        elif self.phEXIT:
            self.wakeOnTimer(enabled=False)
            self.pin_led1.set(LOW)
            return self.goNextState()

    #############################################
    ## STATE_TOOL_NOT_POWERED_DENIED
    #############################################
    def stateToolNotPoweredDenied(self):
        if self.phENTER:
            self.pin_led2.set(HIGH)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'AccessDone':
                return self.exitAndGoto(self.STATE_TOOL_NOT_POWERED)
            return False

        elif self.phEXIT:
            self.pin_led2.set(LOW)
            return self.goNextState()



    #############################################
    ## STATE_RFID_ERROR
    #############################################
    def stateRFIDError(self):
        if self.phENTER:
            self.telemetryEvent.emit('personality/login', json.dumps({'error': True, 'errorText': self._rfidErrorReason}))
            self.pin_led2.set(HIGH)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'AccessDone':
                return self.exitAndGoto(self.STATE_IDLE)

            return False

        elif self.phEXIT:
            self.pin_led2.set(LOW)
            return self.goNextState()

    #############################################
    ## STATE_ACCESS_DENIED
    #############################################
    def stateAccessDenied(self):
        if self.phENTER:
            self.telemetryEvent.emit('personality/login', json.dumps({'allowed': False, 'member': self.activeMemberRecord.name}))
            self.pin_led2.set(HIGH)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'AccessDone':
                return self.exitAndGoto(self.STATE_IDLE)

            return False

        elif self.phEXIT:
            self.pin_led2.set(LOW)
            return self.goNextState()


    #############################################
    ## STATE_ACCESS_ALLOWED
    #############################################
    def stateAccessAllowed(self):
        if self.phENTER:
            self.telemetryEvent.emit('personality/login', json.dumps({'allowed': True, 'member': self.activeMemberRecord.name}))
            self.pin_led1.set(HIGH)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'AccessDone':
                if self._performSafetyCheck:
                    return self.exitAndGoto(self.STATE_SAFETY_CHECK)
                else:
                    self.enableTool()
                    return self.exitAndGoto(self.STATE_TOOL_ENABLED_INACTIVE)

            return False

        elif self.phEXIT:
            self.pin_led1.set(LOW)
            return self.goNextState()


    #############################################
    ## STATE_SAFETY_CHECK
    #############################################
    def stateSafetyCheck(self):
        if self.phENTER:
            self.wakeOnTimer(enabled=True, interval=1500, singleShot=True)
            self.enableTool()
            self.pin_led1.set(HIGH)
            return self.goActive()

        elif self.phACTIVE:
            if self.toolActive():
                self.disableTool()
                return self.exitAndGoto(self.STATE_SAFETY_CHECK_FAILED)

            if self.wakereason == self.REASON_TIMER:
                return self.exitAndGoto(self.STATE_SAFETY_CHECK_PASSED)

            return False

        elif self.phEXIT:
            self.wakeOnTimer(enabled=False)
            self.pin_led1.set(LOW)
            return self.goNextState()

    #############################################
    ## STATE_SAFETY_CHECK_PASSED
    #############################################
    def stateSafetyCheckPassed(self):
        return self.goto(self.STATE_TOOL_ENABLED_INACTIVE)

    #############################################
    ## STATE_SAFETY_CHECK_FAILED
    #############################################
    def stateSafetyCheckFailed(self):
        if self.phENTER:
            self.telemetryEvent.emit('personality/safety', json.dumps({'reason':'Safety check failed', 'member': self.activeMemberRecord.name}))
            self.pin_led2.set(HIGH)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'SafetyFailedDone':
                return self.exitAndGoto(self.STATE_IDLE)

            return False

        elif self.phEXIT:
            self.pin_led2.set(LOW)
            return self.goNextState()

    #############################################
    ## STATE_TOOL_ENABLED_ACTIVE
    #############################################
    def stateToolEnabledActive(self):
        if self.phENTER:
            self.telemetryEvent.emit('personality/activity', json.dumps({'active': True, 'member': self.activeMemberRecord.name}))
            self.toolActiveFlag = True
            self.wakeOnTimer(enabled=True, interval=250, singleShot=False)
            return self.goActive()

        elif self.phACTIVE:
            if not self.toolActive():
                return self.exitAndGoto(self.STATE_TOOL_ENABLED_INACTIVE)

            if self.wakereason == self.REASON_TIMER:
                if self.pin_led1.get() == LOW:
                    self.pin_led1.set(HIGH)
                else:
                    self.pin_led1.set(LOW)

            if self._monitorToolPower and not self.toolPowered():
                return self.exitAndGoto(self.STATE_TOOL_ENABLED_NOT_POWERED)

            return False

        elif self.phEXIT:
            self.pin_led1.set(LOW)
            return self.goNextState()

    #############################################
    ## STATE_TOOL_ENABLED_INACTIVE
    #############################################
    def stateToolEnabledInactive(self):
        if self.phENTER:
            self.telemetryEvent.emit('personality/activity', json.dumps({'active': False, 'member': self.activeMemberRecord.name}))
            self.toolActiveFlag = False
            self.pin_led1.set(HIGH)
            return self.goActive()

        elif self.phACTIVE:
            if self.toolActive():
                return self.exitAndGoto(self.STATE_TOOL_ENABLED_ACTIVE)

            if self.wakereason == self.REASON_UI and self.uievent == 'ToolEnabledDone':
                return self.exitAndGoto(self.STATE_TOOL_DISABLED)

            if self._monitorToolPower and not self.toolPowered():
                return self.exitAndGoto(self.STATE_TOOL_ENABLED_NOT_POWERED)

            return False

        elif self.phEXIT:
            self.pin_led1.set(LOW)
            return self.goNextState()

    #############################################
    ## STATE_TOOL_ENABLED_NOT_POWERED
    #############################################
    def stateToolEnabledNotPowered(self):
        if self.phENTER:
            self.disableTool()
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'ToolEnabledDone':
                return self.exitAndGoto(self.STATE_TOOL_DISABLED)

            return False

        elif self.phEXIT:
            return self.goNextState()


    #############################################
    ## STATE_TOOL_TIMEOUT_WARNING
    #############################################
    def stateToolTimeoutWarning(self):
        pass

    #############################################
    ## STATE_TOOL_TIMEOUT
    #############################################
    def stateToolTimeout(self):
        pass

    #############################################
    ## STATE_TOOL_DISABLED
    #############################################
    def stateToolDisabled(self):
        self.disableTool()
        return self.goto(self.STATE_IDLE)

    #############################################
    ## STATE_REPORT_ISSUE
    #############################################
    def stateReportIssue(self):
        if self.phENTER:
            self.pin_led1.set(LOW)
            self.pin_led2.set(LOW)
            self.wakeOnRFID(True)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'ReportIssueDone':
                return self.exitAndGoto(self.STATE_IDLE)

            return False

        elif self.phEXIT:
            self.wakeOnRFID(False)
            return self.goNextState()


    #############################################
    ## STATE_POWER_LOSS
    #############################################
    def statePowerLoss(self):
        if self.phENTER:
            self.telemetryEvent.emit('system/power', json.dumps({'state': 'lost'}))
            self.initPins()
            return self.goActive()

        elif self.phACTIVE:
            # wait until the UI signals that it is time to shut down (countdown timer)
            # or abort and re-initialize if power comes back before then
            if self.wakereason == self.REASON_UI and self.uievent == 'PowerLossDone':
                self.telemetryEvent.emit('system/power', json.dumps({'state': 'shutdown'}))
                return self.exitAndGoto(self.STATE_SHUT_DOWN)
            elif self.wakereason == self.REASON_POWER_RESTORED:
                self.telemetryEvent.emit('system/power', json.dumps({'state': 'restored'}))
                return self.exitAndGoto(self.STATE_INIT)

            return False

        elif self.phEXIT:
            self.wakeOnTimer(enabled=False)
            return self.goNextState()


    #############################################
    ## STATE_LOCK_OUT
    #############################################
    def stateLockOut(self):

        if self.phENTER:
            self.pin_led1.set(LOW)
            self.pin_led2.set(HIGH)
            self.wakeOnTimer(enabled=True, interval=250, singleShot=True)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_TIMER:
                if self.pin_led1.get() == LOW:
                    self.pin_led1.set(HIGH)
                    self.pin_led2.set(LOW)
                    self.wakeOnTimer(enabled=True, interval=250, singleShot=True)
                else:
                    self.pin_led1.set(LOW)
                    self.pin_led2.set(HIGH)
                    self.wakeOnTimer(enabled=True, interval=250, singleShot=True)

            return False

        elif self.phEXIT:
            self.wakeOnTimer(enabled=False)
            self.pin_led2.set(LOW)
            self.pin_led1.set(LOW)
            return self.goNextState()


    #############################################
    ## STATE_SHUT_DOWN
    #############################################
    def stateShutDown(self):
        self.app.shutdown()
        return False
