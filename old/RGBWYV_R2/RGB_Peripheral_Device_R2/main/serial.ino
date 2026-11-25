void setupSerial() {
  Serial.begin(115200);
  Serial.setTimeout(10);
  while (!Serial) delay(10);  // for nrf52840 with native usb
  Serial.println("Serial initialized");
}