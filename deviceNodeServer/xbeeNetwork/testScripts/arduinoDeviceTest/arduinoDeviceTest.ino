/*
 * menymp
 * Simple script to uploat to arduino that emulates a device for the xbee network
 * nov 2023
 */

const int sensorAnalogPin = 0;
const int outputPin = 13;
int cnt = 0;

void setup() {
  pinMode(outputPin,OUTPUT);
  Serial.begin(9600);
  digitalWrite(outputPin, LOW);
}

void loop() {
  if(Serial.available())
  {
    char recv = Serial.read();

    if(recv == 'a') digitalWrite(outputPin, HIGH);
    if(recv == 'b') digitalWrite(outputPin, LOW);
  }
  if(cnt > 600)
  {
    Serial.print("sensorRead:");
    Serial.print(analogRead(sensorAnalogPin));
    Serial.print(",output:");
    Serial.println(digitalRead(outputPin));
    cnt = 0;
  }
  cnt ++;
  delay(10);
}
