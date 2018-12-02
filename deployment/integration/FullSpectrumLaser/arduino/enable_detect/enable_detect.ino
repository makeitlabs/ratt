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
//
// --------------------------------------------------------------------------
//
// Author: Steve Richardson (steve.richardson@makeitlabs.com)
//
// --------------------------------------------------------------------------
//
// This module acts as 'glue' logic between a Full Spectrum laser cutter and RATT.  It's responsible for monitoring the laser enable
// line, which is an active low signal that drives the laser.  This line will pulse on and off at unpredictable rates depending on
// the geometry of the current cut and whether it is in vector or raster mode.  This code simply tries to detect the presence of any
// activity at all and filter it out to provide a clean active/inactive signal to RATT.
// 
// LASER ENABLE INPUT - pins 2 and 3
// pins 2 and 3 are tied together in hardware.  it may be possible to do this with a single pin but i did not test that or dive into
// the libraries to look at how they were implemented to see if pins could be shared across the capture timer library and the debounce
// library.  we have a ton of I/O so this was the short path to success.
//
// ACTIVE OUTPUT - pin 4
// this is an active high signal which indicates the laser is active, and can be connected directly to one of the isolated inputs
// on the RATT I/O section.
//
// The Arduino should be powered from the laser cutter 5V supply.
//
// --------------------------------------------------------------------------
//
// requires the following Arduino libraries:
//
// CaptureTimer 0.8.0: https://www.arduinolibraries.info/libraries/capture-timer
// MsTimer2 version 1.1.0: https://www.arduinolibraries.info/libraries/ms-timer2
// Bounce2 version 2.52.0: https://www.arduinolibraries.info/libraries/bounce2
//
// These are included in the RATT github repo so that the firmware may be readily rebuilt in the future
//
// Target Board is a knock-off Arduino Nano, Processor is Atmel 328P (Old Bootloader)
//

#include <CaptureTimer.h>
#include <Bounce2.h>

#define PIN_ACTIVE_OUT  4     // output pin to RATT to indicate laser is active
#define PIN_CAPTURE_IN  2     // input pin from laser enable signal, used for capture timer (mainly to detect raster mode pulses)
#define PIN_BOUNCE_IN   3     // input pin from laser enable signal, used for debouncing same signal (mainly to detect vector mode)

#define CAPTURE_PERIOD  500   // sampling period for capture timer frequency counter (milliseconds)
#define DEBOUNCE_PERIOD 500   // debounce time (milliseconds)

Bounce g_debouncer = Bounce();// debouncer object

void setup()
{
  Serial.begin(115200);

  // set up the capture timer to do frequency counting on the capture input
  CaptureTimer::initCapTicks(CAPTURE_PERIOD, PIN_CAPTURE_IN);

  // set up the g_debouncer to do debounce on the debounce input
  g_debouncer.attach(PIN_BOUNCE_IN, INPUT);
  g_debouncer.interval(DEBOUNCE_PERIOD);

  // set up the output pin
  pinMode(PIN_ACTIVE_OUT, OUTPUT);
}


void loop()
{
  uint16_t ticks;
  static bool cap_active = false;
  static bool bounce_active = false;
  
  static bool last_active = true;
  static bool init = false;

  // every CAPTURE_PERIOD this will determine if any counts have occurred and set cap_active=true if so
  // this indicates that raster activity is probably occurring on the laser since it pulses the laser enable
  // rapidly during raster operation
  if (CaptureTimer::getTicks(&ticks) == true) {
    cap_active = (ticks > 0);
  }

  // debouncer processing on the sense input
  // the laser enable signal is active low, so if the debouncer indicates low, the laser has been on and stable for DEBOUNCE_PERIOD,
  // which usually indicates vector cutting is in progress, since the laser is turned on for long periods during vector cuts
  g_debouncer.update();
  bounce_active = (g_debouncer.read() == 0);

  // the laser is considered active if either detection method is indicating true
  bool active = bounce_active | cap_active;

  // detect a change since last polling cycle, if det is in a new state change the output pin and output some debug data on serial
  // this also runs the very first time the loop runs, via the 'init' flag
  if (active != last_active || !init) {
    Serial.print("active=");
    Serial.print(active);
    Serial.print(" bounce_active=");
    Serial.print(bounce_active);
    Serial.print(" cap_active=");
    Serial.println(cap_active);
    
    digitalWrite(PIN_ACTIVE_OUT, active);
    init = true;
  }

  // store the last active state for comparison the next time through the loop  
  last_active = active;
}
