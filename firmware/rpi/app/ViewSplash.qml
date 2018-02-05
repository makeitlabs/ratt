import QtQuick 2.6
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3

Item {
    anchors.fill: parent
    Rectangle {
        anchors.fill: parent
        color: "#ddddff"

        ColumnLayout {
            anchors.fill: parent
            Image {
                Layout.fillWidth: true
                Layout.fillHeight: true
                source: "makeit_logo_150.png"
                fillMode: Image.PreserveAspectFit
            }
        }
    }
}
