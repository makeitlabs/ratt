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
