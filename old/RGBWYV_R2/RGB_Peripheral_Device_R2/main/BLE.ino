void setupBLE_Peripheral() {
  Bluefruit.begin();
  Bluefruit.setTxPower(4);
  Bluefruit.autoConnLed(1);  // disable leds to draw less power
  Bluefruit.Periph.setConnectCallback(connect_callback);
  Bluefruit.Periph.setDisconnectCallback(disconnect_callback);

  bleuart.begin();  // Start BLE UART service

  bledis.setManufacturer(Manufacturer);  // Start Device Information Service
  bledis.setModel(Model);
  bledis.begin();

  startAdv();  // Start advertising
}

void startAdv(void) {

  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);  // Advertising packet
  Bluefruit.Advertising.addTxPower();

  Bluefruit.Advertising.addService(bleuart);  // Include BLE UART 128-bit UUID
  Bluefruit.Advertising.addService(bledis);   // Include Device Information Service 128-bit UUID
  Bluefruit.ScanResponse.addName();           // Secondary Scan Response packet (optional)

  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.setInterval(32, 244);  // in unit of 0.625 ms
  Bluefruit.Advertising.setFastTimeout(30);    // number of seconds in fast mode
  Bluefruit.Advertising.start(0);              // 0 = Don't stop advertising after n seconds
}

void connect_callback(uint16_t conn_handle) {
  BLEisConnected = true;
}

void disconnect_callback(uint16_t conn_handle, uint8_t reason) {
  BLEisConnected = false;
}
