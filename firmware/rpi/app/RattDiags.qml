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

Item {
    property bool simShutdown: False
    property bool simLED1: False
    property bool simLED2: False
    property bool simOUT1: False
    property bool simOUT2: False
    property bool simOUT3: False
    property bool simOUT4: False

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
            width: 600
            height: 100
            border.width: 4
            border.color: "#000000"

            Connections {
                target: personality

                onSimGPIOPinChanged: {
                    switch (pin) {
                    case 27:
                        simShutdown = value;
                        break;
                    case 500:
                        simOUT1 = value;
                        break;
                    case 501:
                        simOUT2 = value;
                        break;
                    case 502:
                        simOUT3 = value;
                        break;
                    case 503:
                        simOUT4 = value;
                        break;
                    case 508:
                        simLED1 = value;
                        break;
                    case 509:
                        simLED2 = value;
                        break;
                    }
                }
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
                RowLayout {
                    Layout.fillWidth: true

                    Rectangle {
                        width: 40
                        height: 20
                        color: simShutdown ? "orange" : "black"
                        Label {
                            anchors.fill: parent
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: "white"
                            text: "SHDN"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }

                    Rectangle {
                        width: 40
                        height: 20
                        color: simLED1 ? "green" : "black"
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
                        width: 40
                        height: 20
                        color: simLED2 ? "red" : "black"
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
                        width: 40
                        height: 20
                        color: simOUT1 ? "blue" : "black"
                        Label {
                            anchors.fill: parent
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: "white"
                            text: "OUT1"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }
                    Rectangle {
                        width: 40
                        height: 20
                        color: simOUT2 ? "blue" : "black"
                        Label {
                            anchors.fill: parent
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: "white"
                            text: "OUT2"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }
                    Rectangle {
                        width: 40
                        height: 20
                        color: simOUT3 ? "blue" : "black"
                        Label {
                            anchors.fill: parent
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: "white"
                            text: "OUT3"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }
                    Rectangle {
                        width: 40
                        height: 20
                        color: simOUT4 ? "blue" : "black"
                        Label {
                            anchors.fill: parent
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            color: "white"
                            text: "OUT4"
                            font.pixelSize: 12
                            font.bold: true
                        }
                    }





                }

            }
        }


        Rectangle {
            id: aclRect
            color: "#444444"
            width: 600
            height: 100
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
                    text: "Total Records: " + acl.numRecords
                }
                Label {
                    color: "#00f000"
                    font.pixelSize: 12
                    text: "Active Records: " + acl.numActiveRecords
                }
                Label {
                    id: aclHash
                    color: "#777777"
                    font.pixelSize: 10
                    text: "Hash: " + acl.hash
                }
            }
        }

        Rectangle {
            id: rfidRect
            color: "#222222"
            width: 600
            height: 100
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
                    font.pixelSize: 12
                }
                Label {
                    id: tagHashText
                    font.pixelSize: 10
                }
                Label {
                    id: tagDebugText
                    font.pixelSize: 10
                }
            }
        }

        Rectangle {
            id: lookupRect
            color: "#222222"
            width: 600
            height: 150
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
                    text: activeMemberRecord.name
                    visible: activeMemberRecord.valid
                }
                Label {
                    font.pixelSize: 10
                    color: "white"
                    text: activeMemberRecord.plan
                    visible: activeMemberRecord.valid
                }
                Label {
                    font.pixelSize: 10
                    color: "white"
                    text: activeMemberRecord.tag
                    visible: activeMemberRecord.valid
                }
                Label {
                    font.pixelSize: 10
                    color: "white"
                    text: activeMemberRecord.allowed ? "Allowed" : "Denied"
                    visible: activeMemberRecord.valid
                }
                Label {
                    font.pixelSize: 10
                    color: "white"
                    text: activeMemberRecord.warningText
                    visible: activeMemberRecord.valid
                }

            }
        }

    }

}
