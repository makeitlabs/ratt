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

ApplicationWindow {
    id: appWindow
    visible: true
    color: "#004488"
    width: 1024
    height: 768

    signal uiEvent(string evt)

    Component.onCompleted: {
        appWindow.uiEvent.connect(personality.slotUIEvent)
    }

    Connections {
        target: personality

        Component.onCompleted: {
            console.info("pers current state" + personality.currentState);
        }

        onCurrentStateChanged: {
            console.info("state changed " + personality.currentState);

        }


        function switchTo(newItem) {
            if (stack.currentItem !== newItem)
                stack.replace(newItem)
        }

        onStateChanged: {
            console.info("current state changed " + state + ":" + phase);

            switch (state) {
            case "Idle":
                switchTo(viewIdle)
                break;
            case "AccessAllowed":
            case "AccessDenied":
            case "RFIDError":
                switchTo(viewAccess)
                break;
            }
        }
    }

    RattSounds {
        id: sound
    }
    ViewIdle {
        id: viewIdle
        visible: false
    }
    ViewAccess {
        id: viewAccess
        visible: false
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

            Keys.onPressed: {
                //sound.keyAudio.play();

                if (event.key === Qt.Key_Escape) {
                    console.log("esc");
                    appWindow.close();
                } else if (event.key === Qt.Key_Down) {
                    console.log("down");
                } else if (event.key === Qt.Key_Up) {
                    console.log("up");
                } else if (event.key === Qt.Key_Return) {
                    console.log("return");

                }
            }


            StackView {
                id: stack
                anchors.top: tool.bottom
                anchors.bottom: status.top
                anchors.left: parent.left
                anchors.right: parent.right
                initialItem: viewIdle

                onCurrentItemChanged: {
                    currentItem.show();
                }
            }
        }
    }

    Loader {
        id: diagsLoader
        anchors.top: root.bottom
        anchors.left: parent.left
        width: parent.width
        height: parent.height - root.height
        anchors.margins: 4

        Component.onCompleted: {
            if (config.General_Diags) {
                diagsLoader.source = "RattDiags.qml"
            }
        }
    }
}
