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

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQuick.Controls.Styles 1.4

View {
    id: root
    name: "Member List"

    Keys.forwardTo: [activeMemberTable]

    function updateActiveKeys() {
        switch(state) {
        case "list":
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
      appWindow.uiEvent('IdleBusyDone');
    }

    function keyEscape(pressed) {
        if (pressed)
            done(false);
        return true;
    }

    function keyUp(pressed) {
        if (pressed)
          timeoutTimer.restart();
        return false;
    }

    function keyDown(pressed) {
        if (pressed)
          timeoutTimer.restart();
        return false;
    }

    function _show() {
        focusTimer.start();
        activeMemberTable.model = acl.activeMemberList
        activeMemberTable.selection.clear();
        activeMemberTable.selection.select(0, 0);
        activeMemberTable.currentRow = 0;

        status.setKeyActives(true, true, true, false);
    }

    function _hide() {
        activeMemberTable.focus = false;
        root.focus = false;
    }

    Timer {
        id: focusTimer
        interval: 100
        running: false
        repeat: false
        onTriggered: {
            activeMemberTable.forceActiveFocus();
        }
    }

    Timer {
        id: timeoutTimer
        interval: 15000
        repeat: false
        running: shown
        onTriggered: {
          done(false);
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 2

        Label {
            Layout.fillWidth: true
            text: "Active Members (" + acl.numActiveRecords + ")"
            font.pixelSize: 11
            font.weight: Font.DemiBold
            color: "#003399"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        TableView {
            id: activeMemberTable
            Layout.fillWidth: true
            Layout.fillHeight: true

            style: TableViewStyle { }
            headerVisible: false
            alternatingRowColors: false

            selectionMode: SelectionMode.SingleSelection

            TableViewColumn {
                role: "name"
                title: "Name"
            }

            itemDelegate: Text {
                text: ' [' + (styleData.row + 1) + ']: ' + styleData.value.replace('.', ' ')
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
              }
            }
        }
    }
}
