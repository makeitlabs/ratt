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

import QtQuick 2.6
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3

View {
    id: root
    name: "Locked Out"

    function _show() {
        status.setKeyActives(false, false, false, false);
    }


    SequentialAnimation {
        running: shown
        loops: Animation.Infinite
        ColorAnimation {
            target: root
            property: "color"
            from: "#0000ff"
            to: "#0000cc"
            duration: 3000
        }
        ColorAnimation {
            target: root
            property: "color"
            from: "#0000cc"
            to: "#0000ff"
            duration: 3000
        }
    }

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
            Layout.fillWidth: true
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
                PropertyAnimation {
                    duration: 5000
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
}
