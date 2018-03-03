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
    name: "Issue"

    keyReturnActive: true
    keyUpActive: true
    keyDownActive: true

    Keys.forwardTo: [issueTable]

    function done() {
        appWindow.uiEvent('ReportIssueDone');
    }

    function keyReturn(pressed) {
        done();
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

    ListModel {
        id: issuesModel

        ListElement {
            name: "Acting funny"
        }
        ListElement {
            name: "Needs maintenance"
        }
        ListElement {
            name: "Does not function"
        }
        ListElement {
            name: "Caught fire"
        }
        ListElement {
            name: "Exploded"
        }
        ListElement {
            name: "Exploded Twice"
        }
    }

    ColumnLayout {
        anchors.fill: parent
        Label {
            Layout.fillWidth: true
            height: 12
            text: "Report an Issue"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 12
            font.weight: Font.DemiBold
            color: "#000000"
            verticalAlignment: Text.AlignVCenter
        }

        TableView {
            id: issueTable
            Layout.fillWidth: true
            Layout.fillHeight: true
            enabled: true
            model: issuesModel

            style: TableViewStyle { }
            headerVisible: false
            alternatingRowColors: false

            selectionMode: SelectionMode.SingleSelection

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
                if (event.key !== Qt.Key_Up && event.key !== Qt.Key_Down) {
                    event.accepted = false;
                }
            }
        }
    }
}
