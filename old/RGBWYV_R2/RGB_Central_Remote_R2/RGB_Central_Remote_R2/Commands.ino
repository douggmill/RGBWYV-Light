////////////////////////////////////////////////////////////////////////////////////////////////////////////////handleComms
//////////////////////////////////////////////User USB_UART///////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////

void handleComms() {
  if (Serial.available()) {
    int inputIndex = 0;
    while (Serial.available()) {
      char ch = (char)Serial.read();

      if (ch == '\n' || ch == '\r') {  // End of the command
        USB_UART[inputIndex] = '\0';   // Null-terminate the string
        break;
      }

      if (inputIndex < BUFFER_SIZE - 1) {  // Check for buffer overflow
        USB_UART[inputIndex++] = ch;       // Append character to input buffer
      } else {
        Serial.println("Error: Buffer overflow");
        memset(USB_UART, 0, BUFFER_SIZE);  // Clear the buffer
      }
    }

    if (strlen(USB_UART) == 0) {
      clientUart.print("Nothing received");  // Ignore empty input
    }
  }
  if (strcmp(USB_UART, "info") == 0) {  // INFO command
    if (Bluefruit.Central.connected() && clientUart.discovered()) {
      checkID();
    } else {
      Serial.println("Error: Not Connected");
    }

  } else if (strcmp(USB_UART, "help") == 0) {  // INFO command
    Serial.println(helpMenu);

  } else if (strcmp(USB_UART, "*idn") == 0) {
    Serial.println(deviceName);

  } else {
    if (Bluefruit.Central.connected() && clientUart.discovered()) {  // send everything else to client
      clientUart.print(USB_UART);
    }
  }

  memset(USB_UART, 0, BUFFER_SIZE);  // Clear input buffer after processing
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
