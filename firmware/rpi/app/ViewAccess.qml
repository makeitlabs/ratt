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
    name: "Access"

    property bool scrollReason: false
    property string failureReason: ""

    function _show() {
        if (activeMemberRecord.valid && activeMemberRecord.allowed) {
            // valid and allowed, only briefly show the allowed screen
            showTimer.interval = 1500;
            showTimer.start();
        } else if (activeMemberRecord.valid && !activeMemberRecord.allowed) {
            // valid but denied, pause and then run the scrolling animation for the reason text
            scrollReason = false;
            delayTimer.start();
            showTimer.interval = 1500;
        } else {
            // RFID error, show it for a medium time period
            showTimer.interval = 2500;
            showTimer.start();
        }
    }

    function done() {
        appWindow.uiEvent('AccessDone');
    }

    Timer {
        id: showTimer
        interval: 10000
        repeat: false
        running: false
        onTriggered: {
            done();
        }
    }

    Timer {
        id: delayTimer
        interval: 1500
        repeat: false
        running: false
        onTriggered: {
            scrollReason = true;
        }
    }

    Connections {
        target: personality
        onInvalidScan: {
            failureReason = reason.toUpperCase();
        }
    }

    Rectangle {
        anchors.fill: parent
        color: activeMemberRecord.allowed ? "#009900" : "#990000"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 4
            visible: activeMemberRecord.valid && activeMemberRecord.allowed

            Label {
                Layout.fillWidth: true
                text: activeMemberRecord.name
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 12
                font.weight: Font.DemiBold
                color: "#dddddd"
            }
            Label {
                Layout.fillWidth: true
                text: "Plan: " + activeMemberRecord.plan
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 10
                font.weight: Font.DemiBold
                color: "#ffffff"
            }
        }
        ColumnLayout {
            id: colDenied
            anchors.fill: parent
            anchors.margins: 4
            visible: activeMemberRecord.valid && !activeMemberRecord.allowed

            Label {
                Layout.fillWidth: true
                text: activeMemberRecord.name
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 12
                font.weight: Font.DemiBold
                color: "#dddddd"
            }
            ScrollView {
                id: sv
                Layout.fillWidth: true
                Layout.preferredWidth: parent.width
                Layout.fillHeight: true
                horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
                verticalScrollBarPolicy: Qt.ScrollBarAlwaysOff

                Label {
                    id: reasonText
                    width: sv.width
                    Layout.fillHeight: true
                    text: activeMemberRecord.warningText
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                    color: "#ffff00"
                }

                SequentialAnimation on flickableItem.contentY {
                    loops: 1
                    running: scrollReason
                    PropertyAnimation {
                        duration: 5000
                        from: 0
                        to: sv.flickableItem.contentHeight - sv.height
                        easing.type: Easing.InOutQuad
                        easing.period: 100
                    }

                    onStopped: {
                        showTimer.start();
                    }
                }
            }
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 4
            visible: !activeMemberRecord.valid

            Label {
                Layout.fillWidth: true
                text: "RFID Read Failure"
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 12
                font.weight: Font.Bold
                color: "#ffffff"
            }
            Label {
                Layout.fillWidth: true
                text: failureReason
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 12
                font.weight: Font.DemiBold
                font.italic: true
                color: "#ffff00"
            }
        }
    }
}
