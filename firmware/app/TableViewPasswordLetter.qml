
import QtQuick 2.6
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtGraphicalEffects 1.0
import QtQuick.Controls.Styles 1.4

TableView {

  function getValue() {
    if (model && currentRow != -1) {
      return model.get(currentRow).text;
    }
    return null;
  }


    model: ListModel {
      ListElement { text: "A" }
      ListElement { text: "B" }
      ListElement { text: "C" }
      ListElement { text: "D" }
      ListElement { text: "E" }
      ListElement { text: "F" }
      ListElement { text: "G" }
      ListElement { text: "H" }
      ListElement { text: "I" }
      ListElement { text: "J" }
      ListElement { text: "K" }
      ListElement { text: "L" }
      ListElement { text: "M" }
      ListElement { text: "N" }
      ListElement { text: "O" }
      ListElement { text: "P" }
      ListElement { text: "Q" }
      ListElement { text: "R" }
      ListElement { text: "S" }
      ListElement { text: "T" }
      ListElement { text: "U" }
      ListElement { text: "V" }
      ListElement { text: "W" }
      ListElement { text: "X" }
      ListElement { text: "Y" }
      ListElement { text: "Z" }
    }

    style: TableViewStyle { }
    headerVisible: false
    alternatingRowColors: false
    __verticalScrollBar.visible: false

    selectionMode: SelectionMode.SingleSelection

    TableViewColumn {
        role: "text"
        title: ""
    }

    itemDelegate: Text {
        text: styleData.value
        elide: styleData.elideMode
        color: styleData.textColor
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: 10
        height: 6
    }
}
