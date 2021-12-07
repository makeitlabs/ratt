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
    signal mqttPublishSubtopicEvent(string subtopic, string msg)

    property string idleBusyView: ""

    Component.onCompleted: {
        appWindow.uiEvent.connect(personality.slotUIEvent)
        appWindow.mqttPublishSubtopicEvent.connect(mqtt.slotPublishSubtopic)
    }

    Connections {
        target: personality

        // switch to the view if not already there
        function switchTo(newItem) {
            if (stack.currentItem !== newItem) {
                stack.currentItem.hide();
                stack.replace(newItem);
            }
        }

        function showCurrentStateView() {
            var curState = personality.currentState;

            var sp = curState.split(".");

            if (sp.length >= 2) {
                var state = sp[0];
                var phase = sp[1];

                switch (state) {
                case "Idle":
                case "NotPowered":
                    switchTo(viewIdle);
                    break;
                case "IdleBusy":
                    switch (idleBusyView) {
                    case "memberList":
                      switchTo(viewMemberList);
                      break;
                    default:
                      switchTo(viewIdle);
                    }
                    break;
                case "NotPoweredDenied":
                    switchTo(viewAccess);
                    break;
                case "AccessAllowed":
                case "RFIDError":
                    switchTo(viewAccess);
                    break;
                case "AccessDenied":
                  if (config.Personality_PasswordEnabled) {
                    switchTo(viewPassword);
                  } else {
                    switchTo(viewAccess);
                  }
                  break;
                case "ReportIssue":
                    switchTo(viewIssue);
                    break;
                case "Homing":
                    switchTo(viewHoming);
                    break;
                case "HomingFailed":
                    switchTo(viewHomingFailed);
                    break;
                case "HomingOverride":
                    switchTo(viewHomingOverride);
                    break;
                case "SafetyCheck":
                    switchTo(viewSafetyCheck);
                    break;
                case "SafetyCheckFailed":
                    switchTo(viewSafetyFailed);
                    break;
                case "ToolEnabledInactive":
                case "ToolEnabledActive":
                case "ToolEnabledNotPowered":
                    switchTo(viewEnabled);
                    break;
                case "PowerLoss":
                    switchTo(viewPowerLoss);
                    break;
                case "ShutDown":
                    break;
                case "LockOut":
		                switchTo(viewLockedOut);
                    break;
                }
            }
        }

        Component.onCompleted: {
            showCurrentStateView();
        }

        onCurrentStateChanged: {
            showCurrentStateView();
        }

        onStateChanged: {
            console.info("current state changed " + state + ":" + phase);

        }
    }

    RattSounds {
        id: sound
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



            StackView {
                id: stack
                anchors.top: tool.bottom
                anchors.bottom: status.top
                anchors.left: parent.left
                anchors.right: parent.right
                initialItem: viewSplash

                onCurrentItemChanged: {
                    if (currentItem)
                      currentItem.show();
                }
                focus: true

                delegate: StackViewDelegate {

                    replaceTransition: StackViewTransition {
                        SequentialAnimation {
                            ScriptAction {
                                script: enterItem.scale = 1
                            }
                            PropertyAnimation {
                                target: enterItem
                                property: "scale"
                                from: 0
                                to: 1
                                duration: 350
                            }
                        }
                        PropertyAnimation {
                            target: exitItem
                            property: "scale"
                            from: 1
                            to: 0
                            duration: 100
                        }
                    }
                }

                ViewSplash {
                    id: viewSplash
                    visible: false
                }
                ViewIdle {
                    id: viewIdle
                    visible: false
                }
                ViewMemberList {
                    id: viewMemberList
                    visible: false
                }
                ViewAccess {
                    id: viewAccess
                    visible: false
                }
                ViewPassword {
                    id: viewPassword
                    visible: false
                }
                ViewHoming {
                    id: viewHoming
                    visible: false
                }
                ViewHomingFailed {
                    id: viewHomingFailed
                    visible: false
                }
                ViewHomingOverride {
                    id: viewHomingOverride
                    visible: false
                }
                ViewSafetyCheck {
                    id: viewSafetyCheck
                    visible: false
                }
                ViewSafetyFailed {
                    id: viewSafetyFailed
                    visible: false
                }
                ViewEnabled {
                    id: viewEnabled
                    visible: false
                }

                ViewIssue {
                    id: viewIssue
                    visible: false
                }
                ViewPowerLoss {
                    id: viewPowerLoss
                    visible: false
                }
            		ViewLockedOut {
            		    id: viewLockedOut
            		    visible: false
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
