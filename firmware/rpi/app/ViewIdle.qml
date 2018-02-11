import QtQuick 2.5
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.2

Rectangle {
    id: root
    anchors.fill: parent
    color: "#eeeeee"

    state: "logo"

    states: [
        State {
            name: "logo"
        },
        State {
            name: "text"
        }
    ]

    transitions: [
        Transition {
            from: "logo"
            to: "text"
            PropertyAnimation {
                target: logo
                properties: "opacity"
                from: 1.0
                to: 0.0
                duration: 500
            }
            PropertyAnimation {
                target: textColumn
                properties: "opacity"
                from: 0.0
                to: 1.0
                duration: 500
            }
        },
        Transition {
            from: "text"
            to: "logo"
            PropertyAnimation {
                target: textColumn
                properties: "opacity"
                from: 1.0
                to: 0.0
                duration: 500
            }
            PropertyAnimation {
                target: logo
                properties: "opacity"
                from: 0.0
                to: 1.0
                duration: 500
            }
        }
    ]

    Timer {
        interval: 5000
        running: true
        repeat: true
        onTriggered: {
            if (root.state == "logo") {
                root.state = "text"
            } else {
                root.state = "logo";
            }
        }
    }

    Image {
        id: logo
        opacity: 1.0
        anchors.fill: parent
        source: "images/makeit_logo_150.png"
        fillMode: Image.PreserveAspectFit
    }

    ColumnLayout {
        id: textColumn
        opacity: 0.0
        anchors.fill: parent
        anchors.margins: 4

        Label {
            Layout.fillWidth: true
            text: "Tool ID"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 12
            font.weight: Font.Normal
            color: "#444444"
        }
        Label {
            Layout.fillWidth: true
            text: "XYZABC"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 14
            font.weight: Font.DemiBold
            color: "#000000"
        }
        Rectangle {
            color: "transparent"
            Layout.fillHeight: true
            Layout.fillWidth: true
        }

        Label {
            Layout.fillWidth: true
            text: "Scan RFID Below"
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 16
            font.weight: Font.Bold
            color: "#000077"
        }
    }
}
