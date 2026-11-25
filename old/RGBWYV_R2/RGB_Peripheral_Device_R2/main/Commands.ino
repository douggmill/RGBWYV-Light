void handleComms() {
  int inputIndex = 0;

  // Read input from BLE UART
  while (bleuart.available()) {
    char ch = (char)bleuart.read();

    if (ch == '\n' || ch == '\r') {  // End of command
      input[inputIndex] = '\0';      // Null-terminate the string
      inputIndex = 0;                // Reset index for next command
      break;
    }

    if (inputIndex < BUFFER_SIZE - 1) {  // Prevent buffer overflow
      input[inputIndex++] = ch;          // Append character to input buffer
    } else {
      bleuart.print("Error: Buffer Overflow");
      inputIndex = 0;
      memset(input, 0, BUFFER_SIZE);
    }
  }

  // Ignore empty input
  if (strlen(input) == 0) {
    bleuart.print("Nothing received");
    return;
  }



  if (strcmp(input, "temp") == 0) {
    // snprintf(buffer, sizeof(BUFFER_SIZE), "Int: %d, Float: %.2f", myInt, myFloat); // concat int and float example
    sensors_event_t humidity, temp;
    aht.getEvent(&humidity, &temp);  // populate temp and humidity objects with fresh data
    bleuart.print(temp.temperature);



  } else if (strcmp(input, "fan0") == 0) {  // extract ints and floats
    pcf.digitalWrite(2, LOW);



  } else if (strcmp(input, "fan1") == 0) {  // extract ints and floats
    pcf.digitalWrite(2, HIGH);



  } else if (strcmp(input, "err?") == 0) {
    snprintf(output, BUFFER_SIZE2, "tempI2C=%d", statusI2C_1);
    bleuart.print(output);
    memset(output, 0, BUFFER_SIZE2);
    snprintf(output, BUFFER_SIZE2, "fanI2C=%d", statusI2C_2);
    bleuart.print(output);
    memset(output, 0, BUFFER_SIZE2);



  } else if (strcmp(input, "val?") == 0) {
    buildAllValuesCSV();
    print_inChunks();



  } else if (strcmp(input, "save") == 0) {
    buildAllValuesCSV();
    saveValuesToFS();



  } else if (strcmp(input, "read") == 0) {
    readValuesFromFS();



  } else if (strcmp(input, "dele") == 0) {
    eraseValuesFile();



  } else if (strncmp(input, "adc", 3) == 0) {  // Handle "adc" group commands
    char* indexStr = strtok(input + 3, ",");   // Extract channel index
    if (indexStr != NULL) {
      int channel = atoi(indexStr);          // Convert index to integer
      if (channel >= 0 && channel <= 58) {   // Valid range
        char* valueStr = strtok(NULL, ",");  // Extract value
        if (valueStr != NULL) {
          float value = atof(valueStr);  // Convert to float
          value = value / 1000.0;
          adc[channel] = value;  // Store in array
          updateGroups(channel);
          //bleuart.print(input);
        } else {
          bleuart.print("Error: Bad ADC value");
        }
      } else {
        bleuart.print("Error: Bad ADC chan");
      }
    } else {
      bleuart.print("Error: Bad ADC format");
    }

  } else if (strncmp(input, "mode,", 5) == 0) {
    bleuart.print(input);
    effectModes = atoi(input + 5);  // Parse mode value
    if (effectModes == 2) {
      writeManual();
    }
    else if (effectModes == 0) {
      setPWMtoZero();
    }
  }
  memset(input, 0, BUFFER_SIZE);  // Clear the buffer for next command
}


// adc[channel] = value;  // V3 Updategroups() goes just bellow where arrays are updated in cmds
// updateGroups(channel);

void updateGroups(int channel) {
  if (channel >= 0 && channel <= 6) {
    for (int i = 0; i < 7; i++) {
      if (i == channel) {
        redMultipliers[i] = adc[i];
      }
    }

  } else if (channel >= 7 && channel <= 13) {
    for (int i = 0; i < 7; i++) {
      if (i + 7 == channel) {
        amberMultipliers[i] = adc[i + 7];
      }
    }

  } else if (channel >= 14 && channel <= 20) {
    for (int i = 0; i < 7; i++) {
      if (i + 14 == channel) {
        greenMultipliers[i] = adc[i + 14];
      }
    }

  } else if (channel >= 21 && channel <= 27) {
    for (int i = 0; i < 7; i++) {
      if (i + 21 == channel) {
        blueMultipliers[i] = adc[i + 21];
      }
    }

  } else if (channel >= 28 && channel <= 34) {
    for (int i = 0; i < 7; i++) {
      if (i + 28 == channel) {
        violetMultipliers[i] = adc[i + 28];
      }
    }

  } else if (channel >= 35 && channel <= 41) {
    for (int i = 0; i < 7; i++) {
      if (i + 35 == channel) {
        upperThresholds[i] = adc[i + 35];
      }
    }

  } else if (channel >= 42 && channel <= 48) {
    for (int i = 0; i < 7; i++) {
      if (i + 42 == channel) {
        lowerThresholds[i] = adc[i + 42];
      }
    }
    if (effectModes == 2) {
      writeManual();
    }

  } else if (channel >= 49 && channel <= 54) {
    if (effectModes == 2) {
      writeManual();
    } else {
      whiteValue = adc[54] * upperThresholds[5] * 100;  // Should be manually adjustable in any mode
    }

  } else if (channel == 55) {
    frequency = 10000.00 * adc[55];
    // frequency = constrain(frequency, 1.0, 10000.00);
    if (effectModes == 2) {
      writeManual();
    }
  }
}



void writeManual() {
  for (int i = 0; i < NUM_OF_PINS; i++) {
    RYGBVW_Values[i] = adc[49 + i] * upperThresholds[i] * 100;
    dutyCycleValues[i] = RYGBVW_Values[i];
  }
  writeFreqAndPWMtoPins();
}
