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
        id: rfidAudio
        source: "audio/sfx061.wav"
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

        Connections {
            target: rfid
            onTagScan: {
                rfidAudio.play()
                var prettyTime = new Date(time * 1000)
                tagText.text = tag + '(' + prettyTime + ')'
            }
        }

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
            RowLayout {
                Label {
                    color: "white"
                    text: "Last RFID Read:"
                }
                Label {
                    id: tagText
                    color: "cyan"
                }
            }
        }
    }
}
