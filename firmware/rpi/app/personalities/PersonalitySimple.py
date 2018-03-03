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

from PersonalityBase import PersonalityBase
from QtGPIO import LOW, HIGH

class Personality(PersonalityBase):
    #############################################
    ## Tool Personality: Simple Tool
    #############################################
    PERSONALITY_DESCRIPTION = 'Simple'

    #############################################
    ## State definitions:
    ##     STATE_NAME = 'StateName'
    #############################################
    STATE_UNINITIALIZED = 'Uninitialized'
    STATE_INIT = 'Init'
    STATE_IDLE = 'Idle'
    STATE_LOCKOUT_CHECK = 'LockoutCheck'
    STATE_ACCESS_DENIED = 'AccessDenied'
    STATE_ACCESS_ALLOWED = 'AccessAllowed'
    STATE_RFID_ERROR = 'RFIDError'
    STATE_SAFETY_CHECK = 'SafetyCheck'
    STATE_SAFETY_CHECK_PASSED = 'SafetyCheckPassed'
    STATE_SAFETY_CHECK_FAILED = 'SafetyCheckFailed'
    STATE_TOOL_ENABLED_INACTIVE = 'ToolEnabledInactive'
    STATE_TOOL_ENABLED_ACTIVE = 'ToolEnabledActive'
    STATE_TOOL_TIMEOUT_WARNING = 'ToolTimeoutWarning'
    STATE_TOOL_TIMEOUT = 'ToolTimeout'
    STATE_TOOL_DISABLED = 'ToolDisabled'

    def __init__(self, *args, **kwargs):
        PersonalityBase.__init__(self, *args, **kwargs)

        #############################################
        ## Map states to state handler functions
        #############################################
        self.states = {self.STATE_UNINITIALIZED : self.stateUninitialized,
                       self.STATE_INIT : self.stateInit,
                       self.STATE_IDLE : self.stateIdle,
                       self.STATE_LOCKOUT_CHECK : self.stateLockoutCheck,
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
                       self.STATE_TOOL_DISABLED : self.stateToolDisabled
                       }

        # Set initial state and phase
        self.state = self.STATE_UNINITIALIZED
        self.statePhase = self.PHASE_ACTIVE

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
        self.pins[4].set(LOW)
        self.pins[5].set(LOW)
        self.pins[6].set(LOW)
        self.pins[7].set(LOW)
        return self.goto(self.STATE_IDLE)

    #############################################
    ## STATE_IDLE
    #############################################
    def stateIdle(self):
        if self.phENTER:
            self.activeMemberRecord.clear()
            self.wakeOnRFID(True)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_RFID_ALLOWED:
                return self.exitAndGoto(self.STATE_ACCESS_ALLOWED)
            elif self.wakereason == self.REASON_RFID_DENIED:
                return self.exitAndGoto(self.STATE_ACCESS_DENIED)
            elif self.wakereason == self.REASON_RFID_ERROR:
                return self.exitAndGoto(self.STATE_RFID_ERROR)

            # otherwise thread goes back to waiting
            return False

        elif self.phEXIT:
            self.wakeOnRFID(False)
            return self.goNextState()

    #############################################
    ## STATE_LOCKOUT_CHECK
    #############################################
    def stateLockoutCheck(self):
        pass

    #############################################
    ## STATE_ACCESS_DENIED
    #############################################
    def stateRFIDError(self):
        if self.phENTER:
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'AccessDone':
                return self.exitAndGoto(self.STATE_IDLE)

            return False

        elif self.phEXIT:
            return self.goNextState()

    #############################################
    ## STATE_ACCESS_DENIED
    #############################################
    def stateAccessDenied(self):
        if self.phENTER:
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'AccessDone':
                return self.exitAndGoto(self.STATE_IDLE)

            return False

        elif self.phEXIT:
            return self.goNextState()


    #############################################
    ## STATE_ACCESS_ALLOWED
    #############################################
    def stateAccessAllowed(self):
        if self.phENTER:
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'AccessDone':
                return self.exitAndGoto(self.STATE_IDLE)

            return False

        elif self.phEXIT:
            return self.goNextState()


    #############################################
    ## STATE_SAFETY_CHECK
    #############################################
    def stateSafetyCheck(self):
        pass

    #############################################
    ## STATE_SAFETY_CHECK_PASSED
    #############################################
    def stateSafetyCheckPassed(self):
        pass

    #############################################
    ## STATE_SAFETY_CHECK_FAILED
    #############################################
    def stateSafetyCheckFailed(self):
        pass

    #############################################
    ## STATE_TOOL_ENABLED_ACTIVE
    #############################################
    def stateToolEnabledActive(self):
        pass

    #############################################
    ## STATE_TOOL_ENABLED_INACTIVE
    #############################################
    def stateToolEnabledInactive(self):
        pass

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
        pass
