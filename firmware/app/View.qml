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

Rectangle {
    id: root

    property bool shown: false
    property string name: "View"

    color: "#dddddd"

    function show() {
        shown = true;
        _show();
        console.debug("view %s shown", name)
        root.forceActiveFocus()
    }

    function _show() {
        // implement this to perform actions when the view is shown
    }

    function hide() {
        shown = false;
        _hide();
        console.debug("view %s hidden", name)
        root.focus=false
    }

    function _hide() {
        // implement this to perform actions when the view is hidden
    }


    function keyEscape(pressed) {
        console.info(name, "esc", pressed);
        return true;
    }
    function keyDown(pressed) {
        console.info(name, "down", pressed);
        return true;
    }
    function keyUp(pressed) {
        console.info(name, "up", pressed);
        return true;
    }
    function keyReturn(pressed) {
        console.info(name, "return", pressed);
        return true;
    }

    function keyHandler(event, pressed) {
        if (status.keyEscActive && event.key === Qt.Key_Escape) {
            return keyEscape(pressed);
        } else if (status.keyDownActive && event.key === Qt.Key_Down) {
            return keyDown(pressed);
        } else if (status.keyUpActive && event.key === Qt.Key_Up) {
            return keyUp(pressed);
        } else if (status.keyReturnActive && event.key === Qt.Key_Return) {
            return keyReturn(pressed);
        }
        return false;
    }

    Keys.onPressed: {
        if (shown) {
            event.accepted = keyHandler(event, true);
        }
    }

    Keys.onReleased: {
        if (shown) {
            event.accepted = keyHandler(event, false);
        }
    }

}
