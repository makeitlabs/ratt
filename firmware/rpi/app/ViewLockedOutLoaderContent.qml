import QtQuick 2.6
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3


ColumnLayout {
  anchors.fill: parent
  Label {
      Layout.fillWidth: true
      text: "Locked Out"
      horizontalAlignment: Text.AlignHCenter
      font.pixelSize: 16
      font.weight: Font.Bold
      color: "#ffcc00"
      topPadding: 2
      bottomPadding: 1
  }

  ScrollView {
    id: sv
    Layout.preferredWidth: parent.width
    Layout.fillHeight: true
    horizontalScrollBarPolicy: Qt.ScrollBarAlwaysOff
    verticalScrollBarPolicy: Qt.ScrollBarAlwaysOff

    Text {
        id: reasonText
        width: sv.width
        text: personality.lockReason
        font.pixelSize: 12
        font.weight: Font.DemiBold
        wrapMode: Text.Wrap
        color: "#ffffff"
        leftPadding: 5
        rightPadding: 5
        elide: Text.ElideRight
        maximumLineCount: 25
    }

    SequentialAnimation on flickableItem.contentY {
        loops: Animation.Infinite
        running: sv.flickableItem.contentHeight > sv.height
        PauseAnimation {
          duration: 1000
        }
        PropertyAnimation {
            duration: 7500
            from: 0
            to: sv.flickableItem.contentHeight - sv.height
            easing.type: Easing.InOutQuad
            easing.period: 100
        }
        PauseAnimation {
          duration: 1000
        }
        PropertyAnimation {
            duration: 1000
            from: sv.flickableItem.contentHeight - sv.height
            to: 0
            easing.type: Easing.InOutQuad
            easing.period: 100
        }
    }
  }
}
