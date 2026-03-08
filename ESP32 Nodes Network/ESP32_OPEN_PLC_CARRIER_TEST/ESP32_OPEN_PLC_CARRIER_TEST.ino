/*
 * Mar 2026
 * menymp
 * simple pin test for open plc esp32 carrier
*/

// N.O. Relay outputs
#define OUT_1_PIN       1 // Shared with UART0 TX
#define OUT_2_PIN       2
#define OUT_3_PIN       3 // Shared with UART0 RX
#define OUT_4_PIN       4
#define OUT_5_PIN       5
#define OUT_6_PIN       12

// OPTOCOUPLED 12 / 24 v Inputs
#define IN_1_PIN        17
#define IN_2_PIN        18
#define IN_3_PIN        19
#define IN_4_PIN        21
#define IN_5_PIN        22
#define IN_6_PIN        23


void setup() {
  // initialize the LED pin as an output:
   /* OUTPUT SETUP */
  pinMode(OUT_1_PIN, OUTPUT);
  pinMode(OUT_2_PIN, OUTPUT);
  pinMode(OUT_3_PIN, OUTPUT);
  pinMode(OUT_4_PIN, OUTPUT);
  pinMode(OUT_5_PIN, OUTPUT);
  pinMode(OUT_6_PIN, OUTPUT);
  /* OUTPUT INITIAL STATES */
  digitalWrite(OUT_1_PIN, 0);
  digitalWrite(OUT_2_PIN, 0);
  digitalWrite(OUT_3_PIN, 0);
  digitalWrite(OUT_4_PIN, 0);
  digitalWrite(OUT_5_PIN, 0);
  digitalWrite(OUT_6_PIN, 0);

  /* INPUT SETUP */
  pinMode(IN_1_PIN, INPUT_PULLUP);
  pinMode(IN_2_PIN, INPUT_PULLUP);
  pinMode(IN_3_PIN, INPUT_PULLUP);
  pinMode(IN_4_PIN, INPUT_PULLUP);
  pinMode(IN_5_PIN, INPUT_PULLUP);
  pinMode(IN_6_PIN, INPUT_PULLUP);
}

void loop() {
  digitalWrite(OUT_1_PIN, 0);
  digitalWrite(OUT_2_PIN, 1);
  digitalWrite(OUT_3_PIN, 0);
  digitalWrite(OUT_4_PIN, 1);
  digitalWrite(OUT_5_PIN, 0);
  digitalWrite(OUT_6_PIN, 1);
  delay(1000);
  digitalWrite(OUT_1_PIN, 1);
  digitalWrite(OUT_2_PIN, 0);
  digitalWrite(OUT_3_PIN, 1);
  digitalWrite(OUT_4_PIN, 0);
  digitalWrite(OUT_5_PIN, 1);
  digitalWrite(OUT_6_PIN, 0);
  delay(1000);
}
