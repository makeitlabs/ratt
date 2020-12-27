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
//
// programming fuse bits:
// https://www.allaboutcircuits.com/projects/atmega328p-fuse-bits-and-an-external-crystal-oscillator/

#include <SoftwareSerial.h>

#define PIN_OUT 4
#define PIN_ANALOG_IN 3

#define WIN_SIZE 196
#define DEAD_BAND 16
#define MIN_COUNT 64
#define CENTER_VALUE 516

#define PIN_SERIAL_OUT 1
#define PIN_SERIAL_IN 0

static char window[WIN_SIZE];


SoftwareSerial softSerial(PIN_SERIAL_IN, PIN_SERIAL_OUT);

void setup() {
  softSerial.begin(9600);
  
  analogReference(DEFAULT);
  pinMode(PIN_OUT, OUTPUT);
  pinMode(PIN_ANALOG_IN, INPUT);
  pinMode(PIN_SERIAL_OUT, OUTPUT);

  softSerial.println("RATT Current Sensor");
  softSerial.println("ESC 3 times to calibrate.");
}

int do_avg(int in)
{
  static int pos = 0;

  window[pos] = (in > (CENTER_VALUE + DEAD_BAND)) | (in < (CENTER_VALUE - DEAD_BAND));
  
  pos++;
  if (pos >= WIN_SIZE)
    pos = 0;

  int sum = 0;
  for (unsigned int i=0; i< WIN_SIZE; i++) {
    if (window[i])
      sum++;
  }

  return sum;
}

void run() {
  int ain = analogRead(PIN_ANALOG_IN);
  int count = do_avg(ain);
  bool on = (count >= MIN_COUNT);

  digitalWrite(PIN_OUT, on ? HIGH : LOW);
}


bool get_char (char *c) {
  if (softSerial.available()) {
    *c = softSerial.read();
    return true;
  }
  return false;
}

#define IWIN_SIZE (WIN_SIZE / 2)
void cal_off_level()
{
  unsigned int* iwindow = (unsigned int*) &window;
  unsigned int min = 65535;
  unsigned int max = 0;

  softSerial.println(F("Acquiring..."));
  for (unsigned int i=0; i < IWIN_SIZE; i++) {
    unsigned int in = analogRead(PIN_ANALOG_IN);
    delay(5);
    iwindow[i] = in;
  }

  softSerial.println(F("Calculating..."));
  unsigned long accum = 0;
  for (unsigned int i=0; i < IWIN_SIZE; i++) {
    unsigned int v = iwindow[i];
    
    if (v < min)
      min = v;

    if (v > max)
      max = v;

    accum += v;
  }

  unsigned int avg = (accum / IWIN_SIZE);

  softSerial.print(F("Window Size="));
  softSerial.println(IWIN_SIZE);
  softSerial.print(F("AVG="));
  softSerial.println(avg);
  softSerial.print(F("MIN="));
  softSerial.println(min);
  softSerial.print(F("MAX="));
  softSerial.println(max);
  softSerial.print(F("DEADBAND="));
  softSerial.println(max - min);
  softSerial.println(F("Cal done."));
}


#define STATE_CAL_INIT 0
#define STATE_CAL_WAIT_MODE 1

bool cal() {
  static unsigned char state = STATE_CAL_INIT;
  char c;
  
  switch (state) {
  case STATE_CAL_INIT:
    softSerial.println(F("Calibrate: 1-OFF Level | 2-Idle Level | 3-On Level | Q-Quit"));
    state = STATE_CAL_WAIT_MODE;
    break;
  case STATE_CAL_WAIT_MODE:
    if (get_char(&c)) {
      switch (c) {
      case '1':
        cal_off_level();
        state = STATE_CAL_INIT;
        break;
        
      case 'q':
      case 'Q':
        softSerial.println("Quit");
        state = STATE_CAL_INIT;
        return false;
      }
    }
    break;
  }

  return true;
}

#define STATE_RUN 0
#define STATE_CAL 1

void loop() {
  static unsigned char state = STATE_RUN;
  static unsigned char esc_count = 0;
  
  switch (state) {
  case STATE_RUN:
    run();
    if (softSerial.available()) {
      char c = softSerial.read();

      if (c == 27) {
        esc_count++;
        if (esc_count >= 3) {
          state = STATE_CAL;
          esc_count = 0;
        }
      }
    }
    
    break;
  case STATE_CAL:
    if (!cal())
      state = STATE_RUN;
    break;
  }

}
