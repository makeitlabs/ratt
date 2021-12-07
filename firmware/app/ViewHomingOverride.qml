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
    name: "Homing Override"

    color: "#440044"

    function _show() {
        showTimer.start();
        sound.homingOverrideAudio.play();
    }

    function done() {
        appWindow.uiEvent('HomingOverrideDone');
    }

    Timer {
        id: showTimer
        interval: 8000
        repeat: false
        running: false
        onTriggered: {
            done();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        Label {
            Layout.fillWidth: true
            text: "HOMING OVERRIDE"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 14
            font.weight: Font.Bold
            color: "#ff0000"
        }
        Label {
            Layout.fillWidth: true
            text: "Not homed in XY!"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 12
            font.weight: Font.DemiBold
            color: "#ffffff"
        }
        Label {
            Layout.fillWidth: true
            text: "PROCEED WITH"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 14
            font.weight: Font.DemiBold
            color: "#ffff00"
        }
        Label {
            Layout.fillWidth: true
            text: "EXTREME CAUTION!"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 14
            font.weight: Font.DemiBold
            color: "#ffff00"
        }

    }
}
