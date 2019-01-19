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

    property bool isToolPowered: false

    function keyEscape(pressed) {
        if (pressed)
            issueTimer.start();
        else
            issueTimer.stop();

        return true;
    }

    function keyReturn(pressed) {
        if (pressed)
          diagTimer.start();
        else
          diagTimer.stop();

        return true;
    }

    Timer {
        id: issueTimer
        interval: 1000
        running: false
        repeat: false
        onTriggered: {
            stop();
            appWindow.uiEvent('ReportIssue');
        }
    }
    Timer {
        id: diagTimer
        interval: 2000
        running: false
        repeat: false
        onTriggered: {
            stop();
            root.state = "diags";
            animTimer.restart();
        }
    }

    state: "logo"

    states: [
        State {
            name: "logo"
        },
        State {
            name: "login"
        },
        State {
            name: "issue"
        },
        State {
            name: "stats"
        },
        State {
            name: "diags"
        }

    ]

    function _show() {
        animTimer.restart()
        root.state = "logo"
        status.keyEscActive = true;
        status.keyReturnActive = true;
        status.keyUpActive = false;
        status.keyDownActive = false;
    }

    Connections {
        target: acl
        onUpdate: {
            root.state = "stats";
            animTimer.restart();
        }
    }

    Connections {
        target: personality

        function checkPersonalityState() {
            var curState = personality.currentState;
            var sp = curState.split(".");

            if (sp.length >= 2) {
                var state = sp[0];
                var phase = sp[1];

                isToolPowered = (state != "NotPowered")
            }
        }

        Component.onCompleted: {
            checkPersonalityState();
        }

        onCurrentStateChanged: {
            checkPersonalityState();
        }
    }

    Timer {
        id: animTimer
        interval: 2500
        running: true
        repeat: true
        onTriggered: {
            if (root.state == "logo") {
                root.state = "login";
            } else if (root.state == "login") {
                if (isToolPowered)
                  root.state = "issue";
                else
                  root.state = "logo";
            } else if (root.state == "issue") {
                root.state = "logo"
            } else if (root.state == "diags") {
                root.state = "stats"
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
            visible: !isToolPowered
            source: "images/bed.png"
            fillMode: Image.PreserveAspectFit
        }
        Image {
            Layout.fillWidth: true
            visible: isToolPowered
            source: "images/makeit_logo_150.png"
            fillMode: Image.PreserveAspectFit
        }

        Label {
            Layout.fillWidth: true
            text: config.General_ToolDesc
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 14
            font.weight: Font.DemiBold
            color: "#000088"
        }
        Label {
            visible: !isToolPowered
            Layout.fillWidth: true
            text: "POWERED OFF"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 14
            font.weight: Font.Bold
            color: "#990000"
        }

    }

    ColumnLayout {
        visible: root.state == "login"
        anchors.fill: parent
        anchors.margins: 4

        Image {
          visible: isToolPowered
          source: "images/rfidlogo.png"
          Layout.fillWidth: true
          Layout.preferredHeight: 50
          fillMode: Image.PreserveAspectFit
        }
        Label {
          visible: isToolPowered
          Layout.fillWidth: true
          text: "Scan RFID Tag Below"
          horizontalAlignment: Text.AlignHCenter
          font.pixelSize: 12
          font.weight: Font.Bold
          color: "#000077"
        }

        Label {
            visible: !isToolPowered
            Layout.fillWidth: true
            text: "POWERED OFF"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 14
            font.weight: Font.Bold
            color: "#990000"
        }
        Label {
            visible: !isToolPowered
            Layout.fillWidth: true
            text: "Turn on power"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 12
            font.weight: Font.Bold
            color: "#222222"
        }
        Label {
            visible: !isToolPowered
            Layout.fillWidth: true
            text: "before you scan"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 12
            font.weight: Font.Bold
            color: "#222222"
        }
        Label {
            visible: !isToolPowered
            Layout.fillWidth: true
            text: "your RFID tag."
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 12
            font.weight: Font.Bold
            color: "#222222"
        }
    }


    ColumnLayout {
        visible: root.state == "stats"
        anchors.fill: parent
        anchors.margins: 4

        Label {
            Layout.fillWidth: true
            text: "TAGS ALLOWED"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 9
            font.weight: Font.DemiBold
            color: "#444444"
        }
        Label {
            Layout.fillWidth: true
            text: acl.numActiveRecords + " / " + acl.numRecords + " total"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 11
            font.weight: Font.Normal
            color: "#000099"
        }
        Label {
            Layout.fillWidth: true
            text: "STATUS"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 9
            font.weight: Font.DemiBold
            color: "#444444"
        }
        Label {
            Layout.fillWidth: true
            text: acl.status
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 11
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

    ColumnLayout {
        visible: root.state == "issue"
        anchors.fill: parent
        anchors.margins: 4

        Label {
            Layout.fillWidth: true
            text: "Found a problem?"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 12
            font.weight: Font.DemiBold
            color: "#990000"
        }

        Label {
            Layout.fillWidth: true
            text: "REPORT AN ISSUE!"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 14
            font.weight: Font.DemiBold
            color: "#990000"
        }

        RowLayout {
          Layout.fillWidth: true
          Rectangle {
            width: 28
            height: 28
            radius: 4
            color: "yellow"
            border.color: "black"
            border.width: 2
            Label {
              anchors.fill: parent
              font.pixelSize: 18
              horizontalAlignment: Text.AlignHCenter
              verticalAlignment: Text.AlignVCenter
              text: "\u2190"
            }
          }

          ColumnLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: "Hold down yellow"
                horizontalAlignment: Text.AlignLeft
                font.pixelSize: 12
                font.weight: Font.Bold
                color: "#444444"
            }
            Label {
                Layout.fillWidth: true
                text: "button to file report"
                horizontalAlignment: Text.AlignLeft
                font.pixelSize: 12
                font.weight: Font.Bold
                color: "#444444"
            }
          }
        }
    }

    ColumnLayout {
        visible: root.state == "diags"
        anchors.fill: parent
        anchors.margins: 4

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
            text: "AP: " + netWorker.currentWifiAP
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

}
