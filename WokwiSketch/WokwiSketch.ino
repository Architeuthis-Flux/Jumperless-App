int attempt = 0;

void setup() {
  delay(1500);
  Serial.begin(115200);
}

void loop() { 
  Serial.print("Attempt: ");
  Serial.println(attempt);
  Serial.println("---");
  Serial.println("I am the very model of a modern Major-General,");
  Serial.println("I've information vegetable, animal, and mineral,");
  Serial.println("I know the kings of England, and I quote the fights historical");
  Serial.println("From Marathon to Waterloo, in order categorical;");
  Serial.flush();
  delay(5000);
  attempt++;
  Serial.println();
}