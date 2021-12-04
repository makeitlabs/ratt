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

import QtQuick 2.5
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.2
import QtQml 2.2

ToolBar {

    property string time: ""

    height: 20

    Label {
        anchors.left: parent.left
        font.pixelSize: 10
        font.weight: Font.DemiBold
        height: 12
        text: time
    }


    Connections {
        target: netWorker

        onWifiStatus: {
            // 'essid', 'freq', 'quality', 'level'

            if (essid == "") {
                wifiSignal.source = "images/wifi_0.png"
                wifiSignal.opacity = 0.2;
            } else {
                wifiSignal.opacity = 1;
                if (quality < 10) {
                    wifiSignal.source = "images/wifi_0.png";
                } else if (quality < 30) {
                    wifiSignal.source = "images/wifi_1.png";
                } else if (quality < 50) {
                    wifiSignal.source = "images/wifi_2.png";
                } else if (quality < 70) {
                    wifiSignal.source = "images/wifi_3.png";
                } else if (quality < 90) {
                    wifiSignal.source = "images/wifi_4.png";
                } else {
                    wifiSignal.source = "images/wifi_5.png";
                }
            }
        }
    }


    Image {
        id: wifiSignal
        anchors.right: dlIndicator.left
        anchors.rightMargin: 5
        source: "images/wifi_0.png"
        opacity: 0.2
    }

    Label {
      id: dlIndicator
      height: 12
      anchors.right: parent.right
      anchors.top: parent.top
      anchors.topMargin: acl.downloadActive ? -2 : acl.errorDescription == "" ? -2 : -2
      anchors.rightMargin: 1
      font.pixelSize: acl.downloadActive ? 16 : acl.errorDescription == "" ? 16 : 14
      font.weight: Font.DemiBold
      text: acl.downloadActive ? "\u21c4" : acl.errorDescription == "" ? "\u2611" : "\u0021"
      color: acl.downloadActive ? "#000000" : acl.errorDescription == "" ? "#33AA33" : "#AA0000"
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
