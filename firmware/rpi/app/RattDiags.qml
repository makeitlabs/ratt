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
import QtMultimedia 5.9
import RATT 1.0

Item {
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
            id: aclRect
            color: "#444444"
            width: 600
            height: 100
            border.width: 4
            border.color: "#000000"

            Connections {
                target: netWorker
                onAclUpdate: {
                    aclTotalText.text = "Total Records: " + total
                    aclActiveText.text = "Active Records: " + active
                    aclHash.text = "Hash: " + hash
                    aclRect.border.color = "#009900"
                }

                onAclUpdateError: {
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
                    id: aclTotalText
                    color: "#999999"
                    font.pixelSize: 12
                }
                Label {
                    id: aclActiveText
                    color: "#00f000"
                    font.pixelSize: 12
                }
                Label {
                    id: aclHash
                    color: "#777777"
                    font.pixelSize: 10
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

                    console.log("error = " + error);
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
                target: appEngine
                onValidScan: {
                    lookupRect.border.color = activeMemberRecord.allowed ? "#009900" : "#990000"
                }
                onInvalidScan: {
                    console.log("invalid scan")
                    lookupRect.border.color = "#999900"
                    invalidReason.text = reason;
                }
            }
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 6
                Label {
                    color: "white"
                    text: "Last Record Lookup"
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
