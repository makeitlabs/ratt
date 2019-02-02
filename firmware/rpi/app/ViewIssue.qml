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
import QtQuick.Controls.Styles 1.4

View {
    id: root
    name: "Issue Report"

    property string currentIssue: ""

    Keys.forwardTo: [issueTable]

    Connections {
        target: personality

        onValidScan: {
            if (root.state == "scan") {
                sound.reportSuccessAudio.play()
                root.state = "thank";
                doneTimer.start();
            }
        }
    }

    function updateActiveKeys() {
        switch(state) {
        case "list":
            status.setKeyActives(true, true, true, true);
            break;
        case "scan":
            status.setKeyActives(true, false, false, false);
            break;
        case "thank":
            status.setKeyActives(false, false, false, false);
        }
    }

    onStateChanged: {
        updateActiveKeys();
    }

    function done(report) {
      if (report) {
        var jo = { issue: currentIssue, member: activeMemberRecord.name }
        appWindow.mqttPublishSubtopicEvent('system/issue', JSON.stringify(jo))
      }
      appWindow.uiEvent('ReportIssueDone');
    }

    function keyEscape(pressed) {
        if (pressed && (state == "list" || state == "scan"))
            done(false);
        return true;
    }

    function keyReturn(pressed) {
        return false;
    }

    function keyUp(pressed) {
        return false;
    }

    function keyDown(pressed) {
        return false;
    }

    function _show() {
        focusTimer.start();
        issueTable.selection.clear();
        issueTable.selection.select(0, 0);
        issueTable.currentRow = 0;

        root.state = "list"
        updateActiveKeys();
    }

    function _hide() {
        issueTable.focus = false;
        root.focus = false;
    }

    Timer {
        id: focusTimer
        interval: 100
        running: false
        repeat: false
        onTriggered: {
            issueTable.forceActiveFocus();
        }
    }

    Timer {
        id: doneTimer
        interval: 2500
        running: false
        repeat: false
        onTriggered: {
            done(true);
        }
    }

    Timer {
        id: timeoutTimer
        interval: 30000
        repeat: false
        running: shown
        onTriggered: {
          appWindow.uiEvent('ReportIssueDone');
        }
    }

    states: [
        State {
            name: "list"
        },
        State {
            name: "scan"
        },
        State {
            name: "thank"
        }
    ]

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 2

        Label {
            Layout.fillWidth: true
            text: "Report an Issue"
            font.pixelSize: 12
            font.weight: Font.DemiBold
            color: "#003399"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        TableView {
            id: issueTable
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.state == "list"

            model: config.Issues

            style: TableViewStyle { }
            headerVisible: false
            alternatingRowColors: false

            selectionMode: SelectionMode.SingleSelection

            selection.onSelectionChanged: {
              if (config.Issues && currentRow != -1) {
                currentIssue = config.Issues[issueTable.currentRow].name;
              }
            }

            TableViewColumn {
                role: "name"
                title: "Name"
            }

            itemDelegate: Text {
                text: styleData.value
                elide: styleData.elideMode
                color: styleData.textColor
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 10
                height: 10
            }

            Keys.onPressed: {
              timeoutTimer.restart();
              if (event.key === Qt.Key_Escape) {
                done(false);
                event.accepted = true;
              } else if (event.key === Qt.Key_Return) {
                if (currentRow == 0) {
                  done(false);
                }

                if (root.state == "list")
                  root.state = "scan";

                event.accepted = true;
              }
            }
        }

        ColumnLayout {
            id: colScan
            visible: root.state == "scan" || root.state == "thank"
            Layout.fillWidth: true
            Layout.fillHeight: true

            Label {
                Layout.fillWidth: true
                visible: root.state == "scan"
                text: currentIssue
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 12
                font.weight: Font.Normal
                color: "#880000"
                verticalAlignment: Text.AlignVCenter
            }

            Label {
                Layout.fillWidth: true
                visible: root.state == "scan"
                text: "Please scan your RFID badge to report the issue."
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 10
                font.weight: Font.Normal
                color: "#000000"
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.Wrap
            }
            Label {
                Layout.fillWidth: true
                visible: root.state == "thank"
                text: activeMemberRecord.name
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 12
                font.weight: Font.DemiBold
                color: "#000099"
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.Wrap
            }
            Label {
                Layout.fillWidth: true
                visible: root.state == "thank"
                text: "Thanks for your report."
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 10
                font.weight: Font.Normal
                color: "#440099"
                verticalAlignment: Text.AlignVCenter
                wrapMode: Text.Wrap
            }

        }
    }
}
