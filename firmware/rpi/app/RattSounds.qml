// --------------------------------------------------------------------------
//  _____       ______________
// |  __ \   /\|__   ____   __|
// | |__) | /  \  | |    | |
// |  _  / / /\ \ | |    | |
// | | \ \/ ____ \| |    | |
// |_|  \_\/    \_\_|    |_|    ... RFID ALL THE THINGS!
//
// A resource access control and telemetry solution for Makerspaces
//
// Developed at MakeIt Labs - New Hampshire's First & Largest Makerspace
// http://www.makeitlabs.com/
//
// Copyright 2018 MakeIt Labs
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the "Software"),
// to deal in the Software without restriction, including without limitation
// the rights to use, copy, modify, merge, publish, distribute, sublicense,
// and/or sell copies of the Software, and to permit persons to whom the
// Software is furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
// WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
// CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
// --------------------------------------------------------------------------
//
// Author: Steve Richardson (steve.richardson@makeitlabs.com)
//

import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import QtMultimedia 5.5
import RATT 1.0

Item {
    property alias keyAudio: keyAudio
    property alias safetyFailedAudio: safetyFailedAudio
    property alias enableAudio: enableAudio
    property alias disableAudio: disableAudio

    property alias timeoutWarningAudio: timeoutWarningAudio

    Component.onCompleted: {
      silence.play()
    }

    SoundEffect {
      id: silence
      source: config.Sound_Silence
      loops: SoundEffect.Infinite
    }

    SoundEffect {
        id: keyAudio
        source: config.Sound_KeyPress
    }
    SoundEffect {
        id: rfidSuccessAudio
        source: config.Sound_RFIDSuccess
    }
    SoundEffect {
        id: rfidFailureAudio
        source: config.Sound_RFIDFailure
    }
    SoundEffect {
        id: rfidErrorAudio
        source: config.Sound_RFIDError
    }
    SoundEffect {
        id: safetyFailedAudio
        source: config.Sound_SafetyFailed
        loops: 3
    }
    SoundEffect {
        id: enableAudio
        source: config.Sound_Enable
    }
    SoundEffect {
        id: disableAudio
        source: config.Sound_Disable
    }
    SoundEffect {
        id: timeoutWarningAudio
        source: config.Sound_TimeoutWarning
    }

    Connections {
        target: personality
        onValidScan: {
            if (personality.currentState === "Idle.ACTIVE") {
                if (record.allowed) {
                    rfidSuccessAudio.play();
                } else {
                    rfidFailureAudio.play();
                }
            }
        }
        onInvalidScan: {
            if (personality.currentState === "Idle.ACTIVE") {
                rfidErrorAudio.play();
            }
        }
    }
}
