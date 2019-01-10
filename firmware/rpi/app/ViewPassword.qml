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
import QtGraphicalEffects 1.0
import QtQuick.Controls.Styles 1.4

View {
    id: root
    name: "Password"

    property bool scrollReason: false
    property bool valid: false
    property string messageText: ""

    states: [
        State {
            name: "pw"
        },
        State {
            name: "correct"
        },
        State {
            name: "incorrect"
        }
    ]

    function updateActiveKeys() {
        switch(state) {
        case "pw":
            status.setKeyActives(true, true, true, true);
            break;
        case "correct":
            status.setKeyActives(false, false, false, false);
            break;
        case "incorrect":
            status.setKeyActives(false, false, false, false);
        }
    }

    onStateChanged: {
        updateActiveKeys();
    }


    function resetTable(t) {
      t.selection.clear();
      t.selection.select(12, 12);
      t.currentRow = 12;

    }

    function resetTables() {
      resetTable(tableA);
      resetTable(tableB);
      resetTable(tableC);
      resetTable(tableD);
    }

    function _show() {
      focusTimer.start();
      resetTables();
      updateActiveKeys();

      root.state = "pw";
    }

    function _hide() {
        tableA.focus = false;
        tableB.focus = false;
        tableC.focus = false;
        tableD.focus = false;
        root.focus = false;
    }

    function checkPassword() {
      var pw = tableA.getValue() + tableB.getValue() + tableC.getValue() + tableD.getValue();
      if (pw == config.Personality_Password) {
        root.state = 'correct';
        messageText = config.Personality_PasswordCorrectText
        scrollReason = false;
        showTimer.interval = 1500;
        delayTimer.start();
        sound.rfidSuccessAudio.play();

      } else {
        root.state = 'incorrect';
        messageText = config.Personality_PasswordIncorrectText
        scrollReason = false;
        showTimer.interval = 1500;
        delayTimer.start();
        sound.rfidFailureAudio.play();
      }
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

    function done() {
        resetTables();

        if (root.state == "correct")
          appWindow.uiEvent('PasswordCorrect');
        else
          appWindow.uiEvent('PasswordIncorrect');
    }

    Timer {
        id: focusTimer
        interval: 100
        running: false
        repeat: false
        onTriggered: {
            tableA.forceActiveFocus();
        }
    }


    Rectangle {
        anchors.fill: parent
        visible: shown
        color: {
          if (root.state == "pw")
            return "#dddddd";
          else if (root.state == "correct")
            return "#007700";
          else if (root.state == "incorrect")
            return "#770000";

        }

        ColumnLayout {
            id: colIncorrect
            anchors.fill: parent
            anchors.margins: 4
            visible: root.state == "correct" || root.state == "incorrect"

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
                    text: messageText
                    font.pixelSize: 14
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                    color: "#ffff00"
                    leftPadding: 10
                    rightPadding: 10
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
          id: colPassword
          anchors.fill: parent
          anchors.margins: 4
          visible: root.state == "pw"

          Label {
              Layout.fillWidth: true
              text: activeMemberRecord.name
              horizontalAlignment: Text.AlignHCenter
              font.pixelSize: 10
              color: "#000000"
          }
          Label {
              Layout.fillWidth: true
              text: config.Personality_PasswordPrompt
              font.pixelSize: 10
              font.weight: Font.DemiBold
              color: "#003399"
              horizontalAlignment: Text.AlignHCenter
              verticalAlignment: Text.AlignVCenter
          }

          RowLayout {
            Layout.fillHeight: true
            Layout.fillWidth: true

            TableViewPasswordLetter {
              id: tableA
              Layout.preferredWidth: 30
              Layout.preferredHeight: 45
              Keys.onPressed: {
                  if (event.key === Qt.Key_Escape) {
                      done();
                      event.accepted = true;
                  } else if (event.key === Qt.Key_Return) {
                    tableB.forceActiveFocus();

                    event.accepted = true;
                  }
              }
            }
            TableViewPasswordLetter {
              id: tableB
              Layout.preferredWidth: 30
              Layout.preferredHeight: 45
              Keys.onPressed: {
                  if (event.key === Qt.Key_Escape) {
                    tableA.forceActiveFocus();
                    event.accepted = true;
                  } else if (event.key === Qt.Key_Return) {
                    tableC.forceActiveFocus();
                    event.accepted = true;
                  }
              }
            }
            TableViewPasswordLetter {
              id: tableC
              Layout.preferredWidth: 30
              Layout.preferredHeight: 45
              Keys.onPressed: {
                  if (event.key === Qt.Key_Escape) {
                    tableB.forceActiveFocus();
                    event.accepted = true;
                  } else if (event.key === Qt.Key_Return) {
                    tableD.forceActiveFocus();
                    event.accepted = true;
                  }
              }
            }
            TableViewPasswordLetter {
              id: tableD
              Layout.preferredWidth: 30
              Layout.preferredHeight: 45
              Keys.onPressed: {
                  if (event.key === Qt.Key_Escape) {
                    tableC.forceActiveFocus();
                    event.accepted = true;
                  } else if (event.key === Qt.Key_Return) {
                    checkPassword();
                    event.accepted = true;
                  }
              }
            }
          }
        }
    }
}
