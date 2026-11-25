void setupPCF8574() { // fan control
  if (!pcf.begin(0x20, &Wire)) {
    statusI2C_2 = 0;
    Serial.println(statusI2C_2);

  } else {
    statusI2C_2 = 1;
    Serial.println(statusI2C_2);
    pcf.pinMode(2, OUTPUT);
    pcf.digitalWrite(2, LOW);
  }
}