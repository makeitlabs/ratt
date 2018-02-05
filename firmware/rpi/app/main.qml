import QtQuick 2.6
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3

ApplicationWindow {
    id: appWindow
    visible: true
    width: 160
    height: 128

    toolBar: RattToolBar {
        id: tool
    }

    statusBar: RattStatusBar {
        id: status
    }

    Item {
        id: root
        anchors.fill: parent
        focus: true

        state: "splash"

        Timer {
            interval: 1500
            repeat: false
            running: true
            onTriggered: {
                root.state = "stack";
            }
        }

        states: [
            State {
                name: "splash"
                PropertyChanges {
                    target: splash; visible: true;
                }
                PropertyChanges {
                    target: stack; visible: false;
                }
                PropertyChanges {
                    target: tool; visible: false;
                }
                PropertyChanges {
                    target: status; visible: false;
                }
            },
            State {
                name: "stack"
                PropertyChanges {
                    target: splash; visible: false;
                }
                PropertyChanges {
                    target: stack; visible: true;
                }
                PropertyChanges {
                    target: tool; visible: true;
                }
                PropertyChanges {
                    target: status; visible: true;
                }
            }
        ]

        Keys.onPressed: {
            if (event.key === Qt.Key_Escape)
                appWindow.close();
            else if (event.key === Qt.Key_Down) {
                appEngine.testUpdateACL();
            } else if (event.key === Qt.Key_Up) {
                appEngine.testPostLog();
            }
        }

        ViewSplash {
            id: splash
            visible: false
        }

        StackView {
            id: stack
            anchors.fill: parent

        }
    }



}
