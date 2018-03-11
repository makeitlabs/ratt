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
    name: "Shutdown"

    color: "#000099"

    property int enabledSecs: 0
    property int activeSecs: 0
    property int idleSecs: 0

    property int idleWarningSecs: 30
    property int idleTimeoutSecs: 60

    property bool idleWarning: (idleSecs < idleWarningSecs)
    property bool idleTimeout: (idleSecs == 0)

    Connections {
        target: personality
        onToolActiveFlagChanged: {
            var isActive = personality.toolActiveFlag;

            status.keyEscActive = !isActive;

            if (isActive)
                idleSecs = idleTimeoutSecs;
        }
    }

    function _show() {
        status.setKeyActives(true, false, false, false);
        enabledSecs = 0;
        activeSecs = 0;
        idleSecs = idleTimeoutSecs;
        updateTime();
    }

    function keyEscape(pressed) {
        if (!personality.toolActiveFlag && pressed) {
            done();
        }
    }


    function done() {
        appWindow.uiEvent('ToolEnabledDone');
    }

    function hhmmss(secs) {
        var sec_num = parseInt(secs, 10);
        var hours   = Math.floor(sec_num / 3600);
        var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
        var seconds = sec_num - (hours * 3600) - (minutes * 60);

        if (hours   < 10) {hours   = "0" + hours;}
        if (minutes < 10) {minutes = "0" + minutes;}
        if (seconds < 10) {seconds = "0" + seconds;}
        return hours + ':' + minutes + ':' + seconds;
    }

    function updateTime() {
        textActiveTime.text = hhmmss(activeSecs);
        textEnabledTime.text=  hhmmss(enabledSecs);
        textIdleTime.text = hhmmss(idleSecs);
    }

    Timer {
        id: idleTimer
        interval: 1000
        repeat: true
        running: shown
        onTriggered: {
            enabledSecs++;
            if (personality.toolActiveFlag)
                activeSecs++;
            else if (idleSecs > 0)
                idleSecs--;
            else if (idleSecs == 0)
                done();

            updateTime();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        Label {
            Layout.fillWidth: true
            text: activeMemberRecord.name
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 16
            font.weight: Font.DemiBold
            color: "#00ffff"
        }

        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.preferredWidth: 35
                text: "TOTAL"
                font.pixelSize: 8
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignRight
                color: "#aaaaaa"
            }

            Label {
                id: textEnabledTime
                Layout.fillWidth: true
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: "#aaaaaa"
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: personality.toolActiveFlag
            Label {
                Layout.preferredWidth: 35
                text: "ACTIVE"
                font.pixelSize: 8
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignRight
                color: "#00ff00"
            }

            Label {
                id: textActiveTime
                Layout.fillWidth: true
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: "#00ff00"
            }
        }

        SequentialAnimation {
            running: !personality.toolActiveFlag && !idleWarning
            loops: Animation.Infinite
            PropertyAnimation {
                target: textIdleTime
                property: "opacity"
                from: 1.0
                to: 0.0
                duration: 100
            }
            PauseAnimation {
                duration: 900
            }
            PropertyAnimation {
                target: textIdleTime
                property: "opacity"
                from: 0.0
                to: 1.0
                duration: 100
            }
            PauseAnimation {
                duration: 900
            }
        }

        SequentialAnimation {
            running: !personality.toolActiveFlag && idleWarning
            loops: Animation.Infinite
            PropertyAnimation {
                target: textIdleTime
                property: "opacity"
                from: 1.0
                to: 0.0
                duration: 50
            }
            PauseAnimation {
                duration: 250
            }
            PropertyAnimation {
                target: textIdleTime
                property: "opacity"
                from: 0.0
                to: 1.0
                duration: 50
            }
            PauseAnimation {
                duration: 250
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: !personality.toolActiveFlag
            Label {
                Layout.preferredWidth: 35
                text: "IDLE"
                font.pixelSize: 8
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignRight
                color: idleWarning ? "#ff3300" : "#aaaa00"
            }

            Label {
                id: textIdleTime
                Layout.fillWidth: true
                font.pixelSize: 22
                font.weight: Font.DemiBold
                color: idleWarning ? "#ff3300" : "#aaaa00"
            }
        }


    }
}
