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

from QtGPIO import LOW, HIGH
from PersonalitySimple import Personality as PersonalitySimple
import simplejson as json

class Personality(PersonalitySimple):
    #############################################
    ## Tool Personality: Laser Cutter
    ##
    ## Supports forcing homing after power-up via detection of the Y limit switch
    ## Homing is enabled via Personality.SafetyCheckEnabled in the .ini
    ## Requires that Personality.MonitorToolPowerEnabled is also enabled
    #############################################
    PERSONALITY_DESCRIPTION = 'LaserCutter'

    STATE_HOMING = 'Homing'
    STATE_HOMING_FAILED = 'HomingFailed'
    STATE_HOMING_OVERRIDE = 'HomingOverride'

    def __init__(self, *args, **kwargs):
        PersonalitySimple.__init__(self, *args, **kwargs)

        # register extra states for this personality
        self.states[self.STATE_HOMING] = self.stateHoming
        self.states[self.STATE_HOMING_FAILED] = self.stateHomingFailed
        self.states[self.STATE_HOMING_OVERRIDE] = self.stateHomingOverride

        self._needsHoming = True

    # returns true if the tool is currently homed (generally connected to the
    # Y limit switch on a laser gantry)
    def toolHomed(self):
        return (self.pins_in[2].get() == 0)

    # returns true if homing requirement should be overridden because of an external
    # condition like using the rotary attachment
    def toolHomingOverride(self):
        return (self.pins_in[3].get() == 1)

    #############################################
    ## STATE_TOOL_NOT_POWERED
    ## For laser cutters, we hook into the tool not powered idle state to
    ## set the 'homing required' flag, so that at next power-up homing must
    ## be done
    #############################################
    def stateToolNotPowered(self):
        if self.phENTER:
            self.logger.info('laser stateToolNotPowered enter')
            self._needsHoming = True

        return super(Personality, self).stateToolNotPowered()

    #############################################
    ## STATE_SAFETY_CHECK
    ## For laser cutters we steal the safety check state to perform XY homing check if needed
    #############################################
    def stateSafetyCheck(self):
        if self._needsHoming:
            return self.goto(self.STATE_HOMING)
        else:
	    self.enableTool()
            return self.goto(self.STATE_TOOL_ENABLED_INACTIVE)

    #############################################
    ## STATE_HOMING
    ## once homed we set the 'needs homing' flag to false since homing will be
    ## valid for the remainder of the time the laser remains powered up
    #############################################
    def stateHoming(self):
        if self.phENTER:
            self.pin_led1.set(HIGH)
            if self.toolActive():
                return self.exitAndGoto(self.STATE_HOMING_FAILED)
            elif self.toolHomingOverride() and self.app.config.value('Personality.HomingExternalOverrideEnabled'):
                return self.exitAndGoto(self.STATE_HOMING_OVERRIDE)
            elif self.toolHomed():
                return self.exitAndGoto(self.STATE_TOOL_ENABLED_INACTIVE)
            return self.goActive()

        elif self.phACTIVE:
            if self._monitorToolPower and not self.toolPowered():
                return self.exitAndGoto(self.STATE_TOOL_NOT_POWERED)

            if self.wakereason == self.REASON_GPIO:
                if self.toolHomed():
                    self._needsHoming = False
		    self.enableTool()
                    return self.exitAndGoto(self.STATE_TOOL_ENABLED_INACTIVE)
                elif self.toolHomingOverride() and self.app.config.value('Personality.HomingExternalOverrideEnabled'):
                    return self.exitAndGoto(self.STATE_HOMING_OVERRIDE)
                elif self.toolActive():
                    return self.exitAndGoto(self.STATE_HOMING_FAILED)

            if self.wakereason == self.REASON_UI:
                if self.uievent == 'HomingAborted' or self.uievent == 'HomingTimeout':
                    return self.exitAndGoto(self.STATE_IDLE)
                elif self.uievent == 'HomingOverride' and self.app.config.value('Personality.HomingManualOverrideEnabled'):
                    return self.exitAndGoto(self.STATE_HOMING_OVERRIDE)

            return False

        elif self.phEXIT:
            self.pin_led1.set(LOW)
            return self.goNextState()

    #############################################
    ## STATE_HOMING_FAILED
    #############################################
    def stateHomingFailed(self):
        if self.phENTER:
            self.telemetryEvent.emit('personality/safety', json.dumps({'reason':'Did not home before activating tool', 'member': self.activeMemberRecord.name}))
            self.pin_led2.set(HIGH)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'HomingFailedDone':
                return self.exitAndGoto(self.STATE_IDLE)

            return False

        elif self.phEXIT:
            self.pin_led2.set(LOW)
            return self.goNextState()

    #############################################
    ## STATE_HOMING_OVERRIDE
    #############################################
    def stateHomingOverride(self):
        if self.phENTER:
            self.telemetryEvent.emit('personality/safety', json.dumps({'reason':'Homing override activated', 'member': self.activeMemberRecord.name}))
            self.pin_led1.set(HIGH)
            self.pin_led2.set(HIGH)
            return self.goActive()

        elif self.phACTIVE:
            if self.wakereason == self.REASON_UI and self.uievent == 'HomingOverrideDone':
		self.enableTool()
                return self.exitAndGoto(self.STATE_TOOL_ENABLED_INACTIVE)
            return False

        elif self.phEXIT:
            self.pin_led1.set(LOW)
            self.pin_led2.set(LOW)
            return self.goNextState()
