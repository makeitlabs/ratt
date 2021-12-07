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
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2
import RATT 1.0
import QtQuick.Controls.Styles 1.4

Item {
    property bool simShutdown: false
    property bool simLED1: false
    property bool simLED2: false
    property bool simOUT0: false
    property bool simOUT1: false
    property bool simOUT2: false
    property bool simOUT3: false

    Component {
      id: bwSwitchStyle
      SwitchStyle {
          groove: Rectangle {
                  implicitWidth: 40
                  implicitHeight: 15
                  radius: 4
                  color: "gray"
                  border.width: 2
          }
          handle: Rectangle {
                  implicitWidth: 20
                  implicitHeight: 15
                  radius: 4
                  color: control.checked ? "white" : "black"
                  border.width: 2
          }
      }
    }

    function updateSimGPIO(pinName, value) {
      switch (pinName) {
      case 'SHUTDOWN':
          simShutdown = value;
          break;
      case 'OUT0':
          simOUT0 = value;
          break;
      case 'OUT1':
          simOUT1 = value;
          break;
      case 'OUT2':
          simOUT2 = value;
          break;
      case 'OUT3':
          simOUT3 = value;
          break;
      case 'LED1':
          simLED1 = value;
          break;
      case 'LED2':
          simLED2 = value;
          break;
      }

    }

    Component.onCompleted: {
      personality.slotForceSimGPIOUpdate();
      personality.slotSimGPIOChangePin('POWER_PRESENT', checkPowerPresent.checked);
      personality.slotSimGPIOChangePin('CHARGE_STATE', checkChargeState.checked);
      personality.slotSimGPIOChangePin('IN0', checkIn0.checked);
      personality.slotSimGPIOChangePin('IN1', checkIn1.checked);
      personality.slotSimGPIOChangePin('IN2', checkIn2.checked);
      personality.slotSimGPIOChangePin('IN3', checkIn3.checked);

//      logConnections.target = logger.signalStreamHandler
    }

    ColumnLayout {
        Label {
            color: "white"
            text: "appWindow size=" + appWindow.width + "x" + appWindow.height
            font.pixelSize: 10
        }
        Label {
            color: "white"
            font.pixelSize: 10
            Component.onCompleted: {
                var gc = tftWindow.mapToGlobal(0, 0);
                text = "tftWindow size=" + tftWindow.width + "x" + tftWindow.height + " x,y=" + gc.x + "," + gc.y;
            }
        }

        Rectangle {
            id: personalityRect
            color: "#444499"
            width: 1015
            height: 50
            border.width: 4
            border.color: "#000000"

            Connections {
                target: personality

                onSimGPIOPinChanged: updateSimGPIO(pinName, value)
            }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 6
                Label {
                    text: "Personality (" + config.Personality_Class + ")"
                    color: "white"
                    font.pixelSize: 12
                    font.bold: true
                }
                Label {
                    color: "cyan"
                    text: "state=" + personality.currentState
                    font.pixelSize: 12
                    font.bold: true
                }
            }
        }


        Rectangle {
          id: simGPIORect
          visible: personality.simGPIO
          color: "#777777"
          width: 1015
          height: personality.simGPIO ? 80 : 0
          border.width: 4
          border.color: "#000000"

          ColumnLayout {
            anchors.fill: parent
            anchors.margins: 6

            Label {
                text: "Simulated GPIO"
                color: "white"
                font.pixelSize: 12
                font.bold: true
            }

            RowLayout {
                Layout.fillWidth: true

                Rectangle {
                    width: 80
                    height: 20
                    color: simShutdown ? "orange" : "black"
                    Label {
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: "white"
                        text: "SHUTDOWN"
                        font.pixelSize: 12
                        font.bold: true
                    }
                }

                Rectangle {
                    width: 80
                    height: 20
                    color: simLED1 ? "#00FF00" : "#005500"
                    Label {
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: "white"
                        text: "LED1"
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
                Rectangle {
                    width: 80
                    height: 20
                    color: simLED2 ? "#FF0000" : "#550000"
                    Label {
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: "white"
                        text: "LED2"
                        font.pixelSize: 12
                        font.bold: true
                    }
                }

                Rectangle {
                    width: 80
                    height: 20
                    color: simOUT0 ? "blue" : "black"
                    Label {
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: "white"
                        text: config.GPIO_OutputNames[0] ? config.GPIO_OutputNames[0] : 'OUT0'
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
                Rectangle {
                    width: 80
                    height: 20
                    color: simOUT1 ? "blue" : "black"
                    Label {
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: "white"
                        text: config.GPIO_OutputNames[1] ? config.GPIO_OutputNames[1] : 'OUT1'
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
                Rectangle {
                    width: 80
                    height: 20
                    color: simOUT2 ? "blue" : "black"
                    Label {
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: "white"
                        text: config.GPIO_OutputNames[2] ? config.GPIO_OutputNames[2] : 'OUT2'
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
                Rectangle {
                    width: 80
                    height: 20
                    color: simOUT3 ? "blue" : "black"
                    Label {
                        anchors.fill: parent
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: "white"
                        text: config.GPIO_OutputNames[3] ? config.GPIO_OutputNames[3] : 'OUT3'
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
            }
            RowLayout {
                Layout.fillWidth: true

                Label {
                  text: 'POWER_PRESENT'
                }
                Switch {
                  id: checkPowerPresent

                  height: 20
                  checked: true
                  onCheckedChanged: {
                    personality.slotSimGPIOChangePin('POWER_PRESENT', checked);
                  }
                  style: bwSwitchStyle
                }
                Rectangle {
                  color: "transparent"
                  width: 10
                }
                Label {
                  text: 'CHARGE_STATE'
                }
                Switch {
                  id: checkChargeState
                  height: 20
                  onCheckedChanged: {
                    personality.slotSimGPIOChangePin('CHARGE_STATE', checked);
                  }
                  style: bwSwitchStyle
                }
                Rectangle {
                  color: "transparent"
                  width: 10
                }
                Label {
                  text: config.GPIO_InputNames[0] ? config.GPIO_InputNames[0] : 'IN0'
                }
                Switch {
                  id: checkIn0
                  height: 20
                  checked: true
                  onCheckedChanged: {
                    personality.slotSimGPIOChangePin('IN0', checked);
                  }
                  style: bwSwitchStyle
                }
                Rectangle {
                  color: "transparent"
                  width: 10
                }
                Label {
                  text: config.GPIO_InputNames[1] ? config.GPIO_InputNames[1] : 'IN1'
                }
                Switch {
                  id: checkIn1
                  height: 20
                  checked: true
                  onCheckedChanged: {
                    personality.slotSimGPIOChangePin('IN1', checked);
                  }
                  style: bwSwitchStyle
                }
                Rectangle {
                  color: "transparent"
                  width: 10
                }
                Label {
                  text: config.GPIO_InputNames[2] ? config.GPIO_InputNames[2] : 'IN2'
                }
                Switch {
                  id: checkIn2
                  height: 20
                  checked: true
                  onCheckedChanged: {
                    personality.slotSimGPIOChangePin('IN2', checked);
                  }
                  style: bwSwitchStyle
                }
                Rectangle {
                  color: "transparent"
                  width: 10
                }
                Label {
                  text: config.GPIO_InputNames[3] ? config.GPIO_InputNames[3] : 'IN3'
                }
                Switch {
                  id: checkIn3
                  height: 20
                  checked: true
                  onCheckedChanged: {
                    personality.slotSimGPIOChangePin('IN3', checked);
                  }
                  style: bwSwitchStyle
                }
            }
          }
        }

        RowLayout {
          width: 1015
          height: 150

          Rectangle {
              id: aclRect
              color: "#222222"
              Layout.fillWidth: true
              Layout.fillHeight: true
              border.width: 4
              border.color: "#000000"

              Connections {
                  target: acl
                  onUpdate: {
                      aclRect.border.color = "#009900"
                  }

                  onUpdateError: {
                      aclRect.border.color = "#990000"
                  }
              }

              ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 6
                  Label {
                      text: "ACL"
                      color: "white"
                      font.pixelSize: 12
                      font.bold: true
                  }
                  Label {
                      color: "#999999"
                      font.pixelSize: 12
                      text: "Total Unique Member Records: " + acl.numRecords
                  }
                  Label {
                      color: "#00f000"
                      font.pixelSize: 12
                      text: "Active Member Records: " + acl.numActiveRecords
                  }
                  Label {
                      color: "#00ffff"
                      font.pixelSize: 12
                      text: "Last status: " + acl.status + " (" + acl.why + ")"
                  }
                  Label {
                      color: "#009999"
                      font.pixelSize: 10
                      text: "Time: " + acl.date
                  }
                  Label {
                      color: "#ff0000"
                      font.pixelSize: 10
                      visible: acl.errorDescription != ""
                      text: "Last error: " + acl.errorDescription
                  }
                  Label {
                      id: aclHash
                      color: "#777777"
                      font.pixelSize: 8
                      text: "Hash: " + acl.hash
                  }
                  Button {
                      text: "Download"
                      onClicked: {
                        acl.setWhy('diag')
                        acl.download()
                      }
                  }

                  Item { Layout.fillHeight: true }
              }
          }

          Rectangle {
              id: rfidRect
              color: "#222222"
              Layout.fillWidth: true
              Layout.fillHeight: true
              border.width: 4
              border.color: "#000000"

              Connections {
                  target: rfid
                  onTagScan: {
                      var prettyTime = new Date(time * 1000);
                      tagTimeText.text = "Time: " + prettyTime;
                      tagTimeText.color = "cyan";

                      tagIDText.text = "Tag: " + tag
                      tagIDText.color = "#00FF00";

                      tagHashText.text = "Hash: " + hash
                      tagHashText.color = "gray";

                      tagDebugText.text = "Debug: " + debugText;
                      tagDebugText.color = "gray";

                      rfidRect.border.color = "#002266";
                  }

                  onTagScanError: {
                      var prettyTime = new Date(time * 1000);
                      tagTimeText.text = "Time: " + prettyTime;
                      tagTimeText.color = "yellow";

                      var errText = "Unknown error";

                      if (error === rfid.errPacket)
                          errText = "Packet structure error";
                      else if (error === rfid.errChecksum)
                          errText = "Checksum error";

                      tagIDText.text = "RFID Read Error: " + errText;
                      tagIDText.color = "#ff0000";

                      tagHashText.text = ""

                      tagDebugText.text = debugText;
                      tagDebugText.color = "white";
                      rfidRect.border.color = "#660000"
                  }
              }


              ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 6
                  Label {
                      color: "white"
                      text: "Last RFID Read"
                      font.pixelSize: 12
                      font.bold: true
                  }
                  Label {
                      id: tagTimeText
                      font.pixelSize: 12
                  }
                  Label {
                      id: tagIDText
                      font.pixelSize: 10
                  }
                  Label {
                      id: tagHashText
                      font.pixelSize: 8
                  }
                  Label {
                      id: tagDebugText
                      font.pixelSize: 10
                  }

                  Item { Layout.fillHeight: true }

                  RowLayout {
                      Layout.preferredHeight: 25
                      Layout.fillWidth: true
                      Rectangle {
                          height: 20
                          width: 100
                          color: "gray"
                          TextInput {
                              id: rfidText
                              anchors.fill: parent
                              text: config.RFID_SimulatedTag
                          }
                      }
                      Button {
                          text: "Sim. Scan"
                          onClicked: {
                              rfid.simulateTagScan(rfidText.text)
                          }
                      }
                      Button {
                          text: "Sim. Scan Error"
                          onClicked: {
                              rfid.simulateScanError(rfidText)
                          }
                      }

                  }
              }
          }

          Rectangle {
              id: lookupRect
              color: "#222222"
              Layout.fillWidth: true
              Layout.fillHeight: true
              border.width: 4
              border.color: "#000000"

              Connections {
                  target: personality
                  onInvalidScan: {
                      lookupRect.border.color = "#999900"
                      invalidReason.text = reason;
                  }
              }

              Connections {
                  target: activeMemberRecord

                  onRecordChanged: {
                      if (!activeMemberRecord.valid) {
                          lookupRect.border.color = "#000000"
                      } else {
                          lookupRect.border.color = activeMemberRecord.allowed ? "#009900" : "#990000"
                      }
                  }
              }
              ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 6
                  Label {
                      color: "white"
                      text: "Active Member Record"
                      font.pixelSize: 12
                      font.bold: true
                  }
                  Label {
                      id: invalidReason
                      font.pixelSize: 12
                      color: "#777777"
                      visible: !activeMemberRecord.valid
                  }

                  Label {
                      font.pixelSize: 10
                      color: "white"
                      text: "logged in: " + activeMemberRecord.loggedIn
                      visible: activeMemberRecord.valid
                  }
                  Label {
                      font.pixelSize: 14
                      color: "yellow"
                      text: activeMemberRecord.name + " (" + activeMemberRecord.plan + ")"
                      visible: activeMemberRecord.valid
                      font.weight: Font.Bold
                  }
                  Label {
                      font.pixelSize: 10
                      color: "white"
                      text: "endorsements: " + activeMemberRecord.endorsements
                      visible: activeMemberRecord.valid
                  }
                  Label {
                      font.pixelSize: 8
                      color: "gray"
                      text: activeMemberRecord.tag
                      visible: activeMemberRecord.valid
                  }
                  Label {
                      font.pixelSize: 10
                      color: activeMemberRecord.allowed ? "green" : "red"
                      text: activeMemberRecord.allowed ? "Allowed" : "Denied"
                      visible: activeMemberRecord.valid
                  }
                  Label {
                      font.pixelSize: 10
                      color: "cyan"
                      text: activeMemberRecord.warningText
                      visible: activeMemberRecord.valid
                  }
                  Item { Layout.fillHeight: true }
              }
          }
        }

        Connections {
          id: logConnections
          target: logger.signalStreamHandler

          onLogEvent: {
            var t= time.substr(time.search(' '));
            t = t.substr(0, t.search(','));

            var body = t + ' ' + name.replace('ratt.', '').toUpperCase() + '-' + level + ' ' + message;
            if (level == 'ERROR') {
              body = '<font color="#ff0000">' + body + '</font>';
            } else if (level == 'WARNING') {
              body = '<font color="#ffff00">' + body + '</font>';
            } else if (level == 'DEBUG') {
              body = '<font color="#00ffff">' + body + '</font>';
            }

            if (name == 'ratt.personality') {
              body = '<b>' + body + '</b>';
            } else if (name == 'ratt.qt') {
              body = '<i><b>' + body + '</b></i>';
            }

            log.append(body);

            const maxlen = 8192
            const removelen = 1024

            if (log.length > maxlen) {
              // remove a bunch of old log
              log.remove(0, log.length - (maxlen-removelen));
              // clean up to the newline
              var nl = log.text.search("\n");
              if (nl != -1) {
                log.remove(0, nl + 1);
              }
            }

            log.cursorPosition = log.length;
          }
        }

        RowLayout {
          width: 1015
          height: 280

          Rectangle {
              id: logRect
              color: "#222222"
              Layout.fillWidth: true
              Layout.fillHeight: true
              border.width: 4
              border.color: "#000000"
              TextArea {
                id: log
                anchors.fill: parent
                Layout.fillWidth: true
                Layout.fillHeight: true
                font.pixelSize: 12
                font.family: 'mono'

                textFormat: TextEdit.RichText
                readOnly: true
                backgroundVisible: false
                textColor: "#ffffff"
              }
          }
        }
    }

}
