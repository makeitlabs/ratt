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

ApplicationWindow {
    id: appWindow
    visible: true
    color: "#004488"
    width: 640
    height: 480

    SoundEffect {
        id: keyAudio
        source: "audio/sfx013.wav"
    }
    SoundEffect {
        id: rfidSuccessAudio
        source: "audio/sfx061.wav"
    }
    SoundEffect {
        id: rfidFailureAudio
        source: "audio/sfx033.wav"
    }

    Rectangle {
        id: root
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        color: "black"
        width: tftWindow.width + 20
        height: tftWindow.height + 20

        Item {
            id: tftWindow
            focus: true
            anchors.centerIn: parent
            width: 160
            height: 128

            RattToolBar {
                id: tool
                width: parent.width
                anchors.top: parent.top
            }

            RattStatusBar {
                id: status
                width: parent.width
                anchors.bottom: parent.bottom
            }

            state: "splash"

            Timer {
                interval: 1500
                repeat: false
                running: true
                onTriggered: {
                    root.state = "stack";
                }
            }

            Keys.onPressed: {
                keyAudio.play();

                if (event.key === Qt.Key_Escape)
                    appWindow.close();
                else if (event.key === Qt.Key_Down) {
                    appEngine.testUpdateACL();
                } else if (event.key === Qt.Key_Up) {
                    appEngine.testPostLog();
                }
            }

            ViewIdle {
                id: viewIdle
                visible: false
            }

            StackView {
                id: stack
                anchors.top: tool.bottom
                anchors.bottom: status.top
                anchors.left: parent.left
                anchors.right: parent.right
                initialItem: viewIdle
            }
        }
    }

    Item {
        anchors.top: root.bottom
        anchors.left: parent.left
        width: parent.width
        height: parent.height - root.height
        anchors.margins: 4

        ColumnLayout {
            Label {
                color: "white"
                text: "appWindow size=" + appWindow.width + "x" + appWindow.height
                font.pixelSize: 10
            }
            Label {
                color: "white"
                text: "tftWindow size=" + tftWindow.width + "x" + tftWindow.height + " x,y=" + tftWindow.x + "," + tftWindow.y
                font.pixelSize: 10
            }

            Rectangle {
                id: aclRect
                color: "#444444"
                width: 600
                height: 100

                Connections {
                    target: netWorker
                    onAclUpdate: {
                        aclTotalText.text = "Total Records: " + total
                        aclActiveText.text = "Active Records: " + active
                        aclHash.text = "Hash: " + hash
                    }

                    onAclUpdateError: {
                    }
                }

                ColumnLayout {
                    anchors.margins: 10
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

                Connections {
                    target: rfid
                    onTagScan: {
                        rfidSuccessAudio.play();
                        var prettyTime = new Date(time * 1000);
                        tagTimeText.text = "Time: " + prettyTime;
                        tagTimeText.color = "cyan";

                        tagIDText.text = "Tag: " + tag
                        tagIDText.color = "#00FF00";

                        tagHashText.text = "Hash: " + hash
                        tagHashText.color = "gray";

                        tagDebugText.text = "Debug: " + debugText;
                        tagDebugText.color = "gray";

                        rfidRect.color = "#002266";
                    }

                    onTagScanError: {
                        rfidFailureAudio.play();
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
                        rfidRect.color = "#660000"
                    }
                }


                ColumnLayout {
                    anchors.margins: 10
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
                color: "#333333"
                width: 600
                height: 150

                Connections {
                    target: appEngine
                    onValidScan: {
                        var level = record['level'];
                        var tagid = record['tagid'];
                        var lastaccessed = record['lastaccessed'];
                        var member = record['member'];
                        var warning = record['warning'];
                        var plan = record['plan'];
                        var allowed = record['allowed'];
                        var nickname = record['nickname'];

                        memberText.text = member;
                        planText.text = plan;
                        tagidText.text = tagid;
                        allowedText.text = allowed;
                        warningText.text = warning;

                        lookupRect.color = (allowed === 'allowed') ? "#007700" : "#770000"
                    }
                }
                ColumnLayout {
                    anchors.margins: 10
                    Label {
                        color: "white"
                        text: "Last Record Lookup"
                        font.pixelSize: 12
                        font.bold: true
                    }
                    Label {
                        id: memberText
                        font.pixelSize: 10
                        color: "white"
                    }
                    Label {
                        id: planText
                        font.pixelSize: 10
                        color: "white"
                    }
                    Label {
                        id: tagidText
                        font.pixelSize: 10
                        color: "white"
                    }
                    Label {
                        id: allowedText
                        font.pixelSize: 10
                        color: "white"
                    }
                    Label {
                        id: warningText
                        font.pixelSize: 10
                        color: "white"
                    }

                }
            }

        }
    }
}
