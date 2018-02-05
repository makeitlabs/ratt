import QtQuick 2.6
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3

StatusBar {
    height: 20

    property string keyEscLabel: "\u274e"
    property string keyDownLabel: "\u25bc"
    property string keyUpLabel: "\u25b2"
    property string keyReturnLabel: "\u2b55"

    RowLayout {
        anchors.fill: parent

        Label {
            Layout.fillHeight: true
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: keyEscLabel
            font.pointSize: 10
            font.weight: Font.Bold
        }
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            color: "#000000"
        }
        Label {
            Layout.fillHeight: true
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: keyDownLabel
            font.pointSize: 8
            font.weight: Font.Bold
        }
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            color: "#000000"
        }
        Label {
            Layout.fillHeight: true
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: keyUpLabel
            font.pointSize: 8
            font.weight: Font.Bold
        }
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 1
            color: "#000000"
        }
        Label {
            Layout.fillHeight: true
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: keyReturnLabel
            font.pointSize: 8
            font.weight: Font.Bold
        }
    }
}
