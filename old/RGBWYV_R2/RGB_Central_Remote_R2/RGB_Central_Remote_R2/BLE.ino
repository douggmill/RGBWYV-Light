void setupBLE_Central() {

  Bluefruit.begin(0, 1);  // Initialize Bluefruit with maximum connections as Peripheral = 0, Central = 1
  Bluefruit.setName(deviceName);


  // Configure DIS client
  clientDis.begin();

  // Init BLE Central Uart Serivce
  clientUart.begin();
  clientUart.setRxCallback(bleuart_rx_callback);

  // Callbacks for Central
  Bluefruit.Central.setConnectCallback(connect_callback);
  Bluefruit.Central.setDisconnectCallback(disconnect_callback);

  /* Start Central Scanning
   * - Enable auto scan if disconnected
   * - Interval = 100 ms, window = 80 ms
   * - Don't use active scan
   * - Start(timeout) with timeout = 0 will scan forever (until connected)
   */
  Bluefruit.Scanner.setRxCallback(scan_callback);
  Bluefruit.Scanner.restartOnDisconnect(true);
  Bluefruit.Scanner.setInterval(160, 80);  // in unit of 0.625 ms
  Bluefruit.Scanner.useActiveScan(false);
  Bluefruit.Scanner.start(0);  // // 0 = Don't stop scanning after n seconds
}

/**
 * Callback invoked when scanner pick up an advertising data
 * @param report Structural advertising data
 */
void scan_callback(ble_gap_evt_adv_report_t* report) {
  // Check if advertising contain BleUart service
  if (Bluefruit.Scanner.checkReportForService(report, clientUart)) {

    // Connect to device with bleuart service in advertising
    Bluefruit.Central.connect(report);
  } else {
    // For Softdevice v6: after received a report, scanner will be paused
    // We need to call Scanner resume() to continue scanning
    Bluefruit.Scanner.resume();
  }
}

/**
 * Callback invoked when an connection is established
 * @param conn_handle
 */
void connect_callback(uint16_t conn_handle) {

  if (clientDis.discover(conn_handle)) {
    memset(manufacturerBuffer, 0, BUFFER_SIZE);
    memset(modelBuffer, 0, BUFFER_SIZE);
    if (clientDis.getManufacturer(manufacturerBuffer, BUFFER_SIZE)) {  // Get and store the Manufacturer Name
      if (strcmp(manufacturerBuffer, Manufacturer) == 0) {
        if (clientDis.getModel(modelBuffer, BUFFER_SIZE)) {  // Get and store the Model Number
          infoAvailable = true;
          checkID();
        }
      } else {
        Serial.println("Error: Model info. -Disconnecting");
        infoAvailable = false;
        Bluefruit.disconnect(conn_handle);
      }
    } else {
      Serial.println("Error: Manufacturer info. -Disconnecting");
      infoAvailable = false;
      Bluefruit.disconnect(conn_handle);
    }
  } else {
    Serial.println("Error: Device info. -Disconnecting");
    infoAvailable = false;
    Bluefruit.disconnect(conn_handle);
  }
  if (clientUart.discover(conn_handle)) {

    clientUart.enableTXD();
    Serial.println("Device Ready");
    // digitalWrite(connectionStatus_LED, LOW);  // turn the LED on (HIGH is the voltage level)
    // sendMode();
    // clientUart.print("err?");

  } else {
    Serial.println("NO BLE FOUND");
    Bluefruit.disconnect(conn_handle);  // disconnect since we couldn't find bleuart service
  }
}


/**
 * Callback invoked when a connection is dropped
 * @param conn_handle
 * @param reason is a BLE_HCI_STATUS_CODE which can be found in ble_hci.h
 */
void disconnect_callback(uint16_t conn_handle, uint8_t reason) {
  (void)conn_handle;
  (void)reason;
  //digitalWrite(connectionStatus_LED, HIGH);  // turn the LED off (LOW is the voltage level)

  Serial.print("Disconnected, reason = 0x");
  Serial.println(reason, HEX);
}

/**
 * Callback invoked when uart received data
 * @param uart_svc Reference object to the service where the data 
 * arrived. In this example it is clientUart
 */
void bleuart_rx_callback(BLEClientUart& uart_svc) {
  Serial.print("[RX]: ");
  while (uart_svc.available()) {
    Serial.print((char)uart_svc.read());
  }
  Serial.println();  //
}