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

import QtQuick 2.6
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3

View {
    id: root
    name: "Homing"

    function _show() {
      status.keyEscActive = true;
      status.keyReturnActive = true;
      status.keyUpActive = false;
      status.keyDownActive = false;

      sound.generalAlertAudio.play();
      gentleReminderTimer.start();
      audioInstructionTimer.start();
      timeoutTimer.start();
    }

    function _hide() {
      timeoutTimer.stop();
      audioInstructionTimer.stop();
      gentleReminderTimer.stop();
      sound.homingInstructionsAudio.stop();
    }

    function keyEscape(pressed) {
      overrideTimer.stop();
      appWindow.uiEvent('HomingAborted');

      return true;
    }

    function keyReturn(pressed) {
      if (pressed)
        overrideTimer.start();
      else
        overrideTimer.stop();

      return true;
    }

    Timer {
      id: overrideTimer
      interval: 3000
      running: false
      repeat: false
      onTriggered: {
          stop();
          appWindow.uiEvent('HomingOverride');
      }
    }

    Timer {
      id: timeoutTimer
      interval: 60000
      running: false
      repeat: false
      onTriggered: {
          stop();
          appWindow.uiEvent('HomingTimeout');
      }
    }

    Timer {
      id: gentleReminderTimer
      interval: 3000
      running: false
      repeat: true
      onTriggered: {
        sound.generalAlertAudio.play();
      }
    }

    Timer {
      id: audioInstructionTimer
      interval: 15000
      running: false
      repeat: true
      onTriggered: {
        sound.homingInstructionsAudio.play();
        interval = 30000;
      }
    }

    Connections {
      target: sound.homingInstructionsAudio

      onPlayingChanged: {
        if (target.playing) {
          gentleReminderTimer.stop();
        } else {
          gentleReminderTimer.start();
        }
      }
    }

    SequentialAnimation {
        running: shown
        loops: Animation.Infinite
        ColorAnimation {
            target: root
            property: "color"
            from: "#cc0000"
            to: "#0000cc"
            duration: 1000
        }
        ColorAnimation {
            target: root
            property: "color"
            from: "#0000cc"
            to: "#cc0000"
            duration: 1000
        }
    }

    ColumnLayout {
        anchors.fill: parent
        Label {
            Layout.fillWidth: true
            text: "HOME GANTRY"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 18
            font.weight: Font.Bold
            color: "#ffffff"
        }
        Label {
            Layout.fillWidth: true
            text: "PRESS XY-0"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 20
            font.weight: Font.DemiBold
            color: "#ffff00"
        }
    }
}
