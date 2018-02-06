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

        Keys.onPressed: {
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
            anchors.fill: parent
            initialItem: viewIdle
        }
    }



}
