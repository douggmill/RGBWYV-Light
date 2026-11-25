static int inputIndex = 0;
static bool discardBleLine = false;

void dispatchBleCommand() {
  if (strcmp(input, "temp") == 0) {
    sensors_event_t humidity, temp;
    aht.getEvent(&humidity, &temp);
    bleuart.print(temp.temperature);
    bleuart.println();

  } else if (strcmp(input, "fan0") == 0) {
    fanState = 0;
    pcf.digitalWrite(2, LOW);

  } else if (strcmp(input, "fan1") == 0) {
    fanState = 1;
    pcf.digitalWrite(2, HIGH);

  } else if (strcmp(input, "err?") == 0) {
    snprintf(output, BUFFER_SIZE2, "tempI2C=%d", statusI2C_1);
    bleuart.println(output);
    memset(output, 0, BUFFER_SIZE2);
    snprintf(output, BUFFER_SIZE2, "fanI2C=%d", statusI2C_2);
    bleuart.println(output);
    memset(output, 0, BUFFER_SIZE2);

  } else if (strcmp(input, "val?") == 0) {
    buildAllValuesCSV();
    print_inChunks();

  } else if (strcmp(input, "save") == 0) {
    buildAllValuesCSV();
    saveValuesToFS();

  } else if (strcmp(input, "read") == 0) {
    readValuesFromFS();
    parseCSVtoADCandEffect();

  } else if (strcmp(input, "dele") == 0) {
    eraseValuesFile();

  } else if (strncmp(input, "adc", 3) == 0) {
    char* indexStr = strtok(input + 3, ",");
    if (indexStr != NULL) {
      int channel = atoi(indexStr);
      if (channel >= 0 && channel <= 58) {
        char* valueStr = strtok(NULL, ",");
        if (valueStr != NULL) {
          float value = atof(valueStr);
          value = value / 1000.0;
          adc[channel] = value;
          updateGroups(channel);
        } else {
          bleuart.println("Error: Bad ADC value");
        }
      } else {
        bleuart.println("Error: Bad ADC chan");
      }
    } else {
      bleuart.println("Error: Bad ADC format");
    }

  } else if (strncmp(input, "mode,", 5) == 0) {
    int newMode = atoi(input + 5);
    if (newMode < 0 || newMode > 3) {
      bleuart.println("Error: Bad mode");
    } else {
      setPWMtoZero();
      resetEffectState();
      effectModes = newMode;
      bleuart.println(input);
      if (effectModes == 2) {
        writeManual();
      }
    }

  } else {
    bleuart.println("Error: Unknown command");
  }
}

void handleComms() {
  while (bleuart.available()) {
    char ch = (char)bleuart.read();

    if (ch == '\r') {
      continue;
    }

    if (ch == '\n') {
      if (discardBleLine) {
        discardBleLine = false;
        memset(input, 0, BUFFER_SIZE);
        inputIndex = 0;
        continue;
      }
      if (inputIndex == 0) {
        continue;
      }
      input[inputIndex] = '\0';
      dispatchBleCommand();
      memset(input, 0, BUFFER_SIZE);
      inputIndex = 0;
      continue;
    }

    if (discardBleLine) {
      continue;
    }

    if (inputIndex < BUFFER_SIZE - 1) {
      input[inputIndex++] = ch;
    } else {
      bleuart.println("Error: Buffer Overflow");
      memset(input, 0, BUFFER_SIZE);
      inputIndex = 0;
      discardBleLine = true;
    }
  }
}

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
      whiteValue = adc[54] * upperThresholds[5] * 100;
    }

  } else if (channel == 55) {
    frequency = 10000.00 * adc[55];
    frequency = constrain(frequency, 1.0, 10000.00);
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
