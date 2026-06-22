void setup() {
Serial.begin(115200);
delay(1200);
pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
Serial.println(millis()+"fuck");
delay(120);
digitalWrite(LED_BUILTIN, LOW);
delay(220);
digitalWrite(LED_BUILTIN, HIGH);
}