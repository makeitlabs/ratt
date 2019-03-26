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
// Copyright 2018-2019 MakeIt Labs
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
// requires ATTiny support for Arduino:
// see https://github.com/damellis/attiny
// see http://highlowtech.org/?p=1695
//
// programmed via ICSP pins using AVR Dragon or other ICSP tools

#define PIN_OUT 4
#define PIN_ANALOG_IN 3
#define PIN_LED 1

#define AVG_SIZE 256
#define DEAD_BAND 8
#define MIN_COUNT 64

void setup() {
  analogReference(DEFAULT);
  pinMode(PIN_OUT, OUTPUT);
  pinMode(PIN_ANALOG_IN, INPUT);
  pinMode(PIN_LED, OUTPUT);
}

int do_avg(int in)
{
  static bool window[AVG_SIZE];
  static int pos = 0;

  window[pos] = (in > (512 + DEAD_BAND)) | (in < (512 - DEAD_BAND));
  
  pos++;
  if (pos >= AVG_SIZE)
    pos = 0;

  int sum = 0;
  for (unsigned int i=0; i< AVG_SIZE; i++) {
    if (window[i])
      sum++;
  }

  return sum;
}

void loop() {
  int ain = analogRead(PIN_ANALOG_IN);
  int count = do_avg(ain);

  bool on = (count >= MIN_COUNT);

  digitalWrite(PIN_OUT, on ? HIGH : LOW);
}
