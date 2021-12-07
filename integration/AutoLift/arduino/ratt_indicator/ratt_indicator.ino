#include <FastLED.h>
#include <ctype.h>

#define NUM_LEDS 18
#define DATA_PIN 2
CRGB leds[NUM_LEDS];

#define SERIAL_BUF_LEN 64

#define STATE_OFF       0
#define STATE_INACTIVE  1
#define STATE_ACTIVE    2
#define STATE_INVALID   9999

unsigned int cur_state = STATE_OFF;

void setup() {
  delay(250);

  FastLED.addLeds<WS2812B, DATA_PIN, GRB>(leds, NUM_LEDS);

  Serial.begin(9600);
}

void parse_serial(char *cmd) {
  if (strcmp(cmd, "TOOLENABLEDINACTIVE.ACTIVE") == 0) {
    cur_state = STATE_INACTIVE;
  } else if (strcmp(cmd, "TOOLENABLEDACTIVE.ACTIVE") == 0) {
    cur_state = STATE_ACTIVE;
  } else {
    cur_state = STATE_OFF;
  }
}

void poll_serial() {
  static char buf[SERIAL_BUF_LEN];
  static unsigned int buf_idx = 0;

  while (Serial.available()) {
    char b = Serial.read();
    if (b == '\n') b = '\0';
    
    if (buf_idx < SERIAL_BUF_LEN-1 || b == '\0') {
      buf[buf_idx++] = toupper(b);
    } 

    if (b == '\0') {
      parse_serial(buf);
      buf_idx = 0;
    }
  }
}

#define PATTERN_SIZE 108
void update_leds() {

  switch (cur_state) {
    case STATE_OFF:
      fill_solid(leds, NUM_LEDS, CRGB::Black);
      break;
    case STATE_INACTIVE:
      fill_solid(leds, NUM_LEDS, CRGB::Green);
      break;
    case STATE_ACTIVE:
      fill_solid(leds, NUM_LEDS, CRGB::Red);
      break;
  }

  FastLED.show();
}

void loop() {
  static unsigned int last_state = STATE_INVALID;
      
  poll_serial();

  if (cur_state != last_state) {
    last_state = cur_state;
    update_leds();
  }
}
