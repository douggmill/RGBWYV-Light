void setupSerial() {
  Serial.begin(921600);
  Serial.setTimeout(1);
  while (!Serial) delay(10);  // for nrf52840 with native usb
  Serial.println("Serial initialized");
}
