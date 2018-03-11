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

View {
    id: root
    name: "Idle"

    function keyEscape(pressed) {
        if (pressed)
            issueTimer.start();
        else
            issueTimer.stop();

        return true;
    }

    function keyReturn(pressed) {
        if (pressed) {
            acl.download();
        }
    }

    Timer {
        id: issueTimer
        interval: 2000
        running: false
        repeat: false
        onTriggered: {
            stop();
            appWindow.uiEvent('ReportIssue');
        }
    }


    state: "logo"

    states: [
        State {
            name: "logo"
        },
        State {
            name: "text"
        },
        State {
            name: "stats"
        }

    ]

    function _show() {
        animTimer.restart()
        root.state = "logo"
        status.keyEscActive = true;
        status.keyReturnActive = true;
    }

    Connections {
        target: acl
        onUpdate: {
            root.state = "stats";
            animTimer.restart();
        }
    }


    Timer {
        id: animTimer
        interval: 3000
        running: true
        repeat: true
        onTriggered: {
            if (root.state == "logo") {
                root.state = "text";
            } else if (root.state == "text") {
                root.state = "stats";
            } else {
                root.state = "logo";
            }
        }
    }

    ColumnLayout {
        visible: root.state == "logo"
        anchors.fill: parent
        anchors.margins: 4

        Image {
            Layout.fillWidth: true
            source: "images/makeit_logo_150.png"
            fillMode: Image.PreserveAspectFit
        }

        Label {
            Layout.fillWidth: true
            text: "ESSID: " + netWorker.currentWifiESSID
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 10
            font.weight: Font.DemiBold
            color: "#444444"
        }
        Label {
            Layout.fillWidth: true
            text: "IP: " + netWorker.currentIfcAddr
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 10
            font.weight: Font.DemiBold
            color: "#444444"
        }
    }

    ColumnLayout {
        visible: root.state == "text"
        anchors.fill: parent
        anchors.margins: 4

        Label {
            Layout.fillWidth: true
            text: "Tool ID"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 12
            font.weight: Font.Normal
            color: "#444444"
        }
        Label {
            Layout.fillWidth: true
            text: config.General_ToolDesc
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 14
            font.weight: Font.DemiBold
            color: "#000000"
        }
        Rectangle {
            color: "transparent"
            Layout.fillHeight: true
            Layout.fillWidth: true
        }

        Label {
            Layout.fillWidth: true
            text: "Scan RFID Below"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 16
            font.weight: Font.Bold
            color: "#000077"
        }
    }

    ColumnLayout {
        visible: root.state == "stats"
        anchors.fill: parent
        anchors.margins: 4

        Label {
            Layout.fillWidth: true
            text: "Members Allowed"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 8
            font.weight: Font.DemiBold
            color: "#444444"
        }
        Label {
            Layout.fillWidth: true
            text: acl.numActiveRecords + " / " + acl.numRecords + " total"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 10
            font.weight: Font.Normal
            color: "#000099"
        }
        Label {
            Layout.fillWidth: true
            text: "Status"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 8
            font.weight: Font.DemiBold
            color: "#444444"
        }
        Label {
            Layout.fillWidth: true
            text: acl.status
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 10
            font.weight: Font.Normal
            color: "#000099"
        }
        Label {
            Layout.fillWidth: true
            text: acl.date
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 10
            font.weight: Font.Normal
            color: "#000099"
        }
    }

}
