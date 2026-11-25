////////////////////////////////////////////////////////////////////////////////////////////////////////////////handleComms
//////////////////////////////////////////////User USB_UART///////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////

static bool discardUsbLine = false;

void dispatchUsbCommand() {
  if (strcmp(USB_UART, "info") == 0) {
    if (Bluefruit.Central.connected() && clientUart.discovered()) {
      checkID();
    } else {
      Serial.println("Error: Not Connected");
    }

  } else if (strcmp(USB_UART, "help") == 0) {
    Serial.println(helpMenu);

  } else if (strcmp(USB_UART, "*idn") == 0) {
    Serial.println(deviceName);

  } else if (Bluefruit.Central.connected() && clientUart.discovered()) {
    // Forward a complete line, including the newline the peripheral waits for.
    clientUart.println(USB_UART);
  } else {
    Serial.println("Error: Not Connected");
  }
}

void handleComms() {
  while (Serial.available()) {
    char ch = (char)Serial.read();

    if (ch == '\r') {
      continue;  // treat CRLF as a single terminator
    }

    if (ch == '\n') {
      if (discardUsbLine) {
        discardUsbLine = false;
        memset(USB_UART, 0, BUFFER_SIZE);
        inputIndex = 0;
        continue;
      }
      if (inputIndex == 0) {
        continue;  // ignore bare/extra newlines
      }
      USB_UART[inputIndex] = '\0';
      dispatchUsbCommand();
      memset(USB_UART, 0, BUFFER_SIZE);
      inputIndex = 0;
      continue;
    }

    if (discardUsbLine) {
      continue;
    }

    if (inputIndex < BUFFER_SIZE - 1) {
      USB_UART[inputIndex++] = ch;
    } else {
      Serial.println("Error: Buffer overflow");
      memset(USB_UART, 0, BUFFER_SIZE);
      inputIndex = 0;
      discardUsbLine = true;
    }
  }
}

void checkID() {
  if (infoAvailable) {
    Serial.print(" Manufacturer: ");
    Serial.println(manufacturerBuffer);
    Serial.print("Model: ");
    Serial.println(modelBuffer);
  } else {
    Serial.println("Device info unavailable.");
  }
}
