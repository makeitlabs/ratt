import QtQuick 2.6
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQml 2.2

ToolBar {

    property string time: ""

    height: 20

    Label {
        anchors.left: parent.left
        font.pixelSize: 12
        height: 12
        text: time
    }

    Image {
        anchors.right: parent.right
        source: "images/wifi_3.png"
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: {
            var d = new Date();
            time = d.toLocaleString(Qt.locale(), "MMM d h:mm:ssAP");
        }
    }

}
