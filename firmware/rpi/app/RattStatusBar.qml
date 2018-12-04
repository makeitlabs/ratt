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
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.2

StatusBar {
    height: 20

    property string keyEscLabel: "\u2190"
    property string keyDownLabel: "\u25bc"
    property string keyUpLabel: "\u25b2"
    property string keyReturnLabel: "\u25cf"

    property bool keyEscActive: false
    property bool keyDownActive: false
    property bool keyUpActive: false
    property bool keyReturnActive: false

    property color activeKeyColor: "#000000"
    property color inactiveKeyColor: "#999999"

    function setKeyActives(esc, down, up, ret) {
        keyEscActive = esc;
        keyDownActive = down;
        keyUpActive = up;
        keyReturnActive = ret;
    }

    RowLayout {
        anchors.fill: parent

        Label {
            Layout.fillHeight: true
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: keyEscLabel
            font.pointSize: 10
            font.weight: Font.Bold
            color: keyEscActive ? activeKeyColor : inactiveKeyColor
        }
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            color: "#000000"
        }
        Label {
            Layout.fillHeight: true
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: keyDownLabel
            font.pointSize: 10
            font.weight: Font.Bold
            color: keyDownActive ? activeKeyColor : inactiveKeyColor
        }
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            color: "#000000"
        }
        Label {
            Layout.fillHeight: true
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: keyUpLabel
            font.pointSize: 10
            font.weight: Font.Bold
            color: keyUpActive ? activeKeyColor : inactiveKeyColor
        }
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            color: "#000000"
        }
        Label {
            Layout.fillHeight: true
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: keyReturnLabel
            font.pointSize: 10
            font.weight: Font.Bold
            color: keyReturnActive ? activeKeyColor : inactiveKeyColor
        }
    }
}
