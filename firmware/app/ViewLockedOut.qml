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
    anchors.fill: parent

    function _show() {
        status.setKeyActives(false, false, false, false);
        loader.source = "ViewLockedOutLoaderContent.qml";
    }

    function _hide() {
      loader.sourceComponent = undefined;
    }

    Connections {
      target: personality

      onLockReasonChanged: {
        loader.sourceComponent = undefined;
        loader.source = "ViewLockedOutLoaderContent.qml"
      }
    }

    SequentialAnimation {
        running: shown
        loops: Animation.Infinite
        ColorAnimation {
            target: root
            property: "color"
            from: "#ffa50a"
            to: "#ff6a68"
            duration: 3000
        }
        ColorAnimation {
            target: root
            property: "color"
            from: "#ff6868"
            to: "#ffa50a"
            duration: 3000
        }
    }

    // this is loaded dynamically because the scroller wasn't properly re-scaling
    // for larger messages... seems the scaling is set at load time, so forcing it
    // to reload makes it work right.
    Loader {
      id: loader
      anchors.fill: parent
    }
}
