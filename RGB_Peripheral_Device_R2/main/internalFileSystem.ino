void setupInternalFS() {

  if (!InternalFS.begin()) {
    bleuart.println("Failed to init FS");
    // while (1) { delay(10); }

  } else {
    bleuart.println("FS initialized");
    // Serial.println("InternalFS initialized");

    if (!InternalFS.exists("data.txt")) {
      buildAllValuesCSV();
      file = InternalFS.open("data.txt", FILE_O_WRITE);
      if (file) {
        file.println(allValuesCSV);
        file.close();
      }
    }
  }
  if (readValuesFromFS()) {
    parseCSVtoADCandEffect();
  }
}



void saveValuesToFS() {

  eraseValuesFile();
  file = InternalFS.open("data.txt", FILE_O_WRITE);

  if (!file) {
    bleuart.println("Failed to open file!");
    return;
  }

  bleuart.println("Writing to file...");
  file.println(allValuesCSV);  // Write the String
  file.close();

  bleuart.println("Write complete.");
}


bool readValuesFromFS() {
  allValuesCSV = "";  // Clear any previous value

  file = InternalFS.open("data.txt", FILE_O_READ);
  if (file) {
    bleuart.println("Reading file contents:");
    while (file.available()) {
      char c = file.read();
      allValuesCSV += c;  // Append each character to the String
    }
    file.close();

    print_inChunks();
    return true;
  }

  bleuart.println("Failed to read FS!");
  return false;
}



void buildAllValuesCSV() {
  allValuesCSV = "";  // Clear existing content

  // One schema: all 59 adc[] values as thousandths, then effectModes.
  // Do not save derived duty-cycle or frequency numbers.
  for (int i = 0; i < 59; i++) {
    allValuesCSV += String((int)(adc[i] * 1000));
    allValuesCSV += ",";
  }
  allValuesCSV += String(effectModes);
}



void parseCSVtoADCandEffect() {
  int lastIndex = 0;
  int commaIndex;
  for (int i = 0; i < 59; i++) {
    commaIndex = allValuesCSV.indexOf(',', lastIndex);
    if (commaIndex == -1) break;  // Safety check
    adc[i] = allValuesCSV.substring(lastIndex, commaIndex).toFloat() / 1000.0;
    lastIndex = commaIndex + 1;
  }

  // Get the last value for effectModes
  String lastValue = allValuesCSV.substring(lastIndex);
  effectModes = lastValue.toInt();

  for (int i = 0; i < 7; i++) {
    redMultipliers[i] = adc[i];
    amberMultipliers[i] = adc[i + 7];
    greenMultipliers[i] = adc[i + 14];
    blueMultipliers[i] = adc[i + 21];
    violetMultipliers[i] = adc[i + 28];
    upperThresholds[i] = adc[i + 35];
    lowerThresholds[i] = adc[i + 42];
  }

  for (int i = 0; i < 6; i++) {
    RYGBVW_Values[i] = adc[i + 49];
  }
  whiteValue = adc[54] * 100.0;
  frequency = adc[55] * 10000.00;
  frequency = constrain(frequency, 1.0, 10000.00);

  // Apply loaded values to the running effect / PWM.
  resetEffectState();
  if (effectModes == 2) {
    writeManual();
  } else {
    setPWMtoZero();
  }
}



void eraseValuesFile() {
  if (InternalFS.remove("data.txt")) {
    bleuart.println("File deleted.");
  } else {
    bleuart.println("Failed to delete file.");
  }
}


void print_inChunks() {
  int count = 0;
  int lastIndex = 0;
  int currentIndex = 0;
  String value;
  String chunk = "";

  while (true) {
    currentIndex = allValuesCSV.indexOf(',', lastIndex);

    // Handle final value (no comma left)
    if (currentIndex == -1) {
      value = allValuesCSV.substring(lastIndex);
      chunk += value;
      bleuart.print(chunk);  // Final chunk, no trailing comma
      break;
    }

    value = allValuesCSV.substring(lastIndex, currentIndex);
    chunk += value;
    count++;

    if (count % 4 == 0) {
      chunk += ",";  // Add comma at end of each full chunk
      bleuart.print(chunk);
      chunk = "";
    } else {
      chunk += ",";  // Comma between values
    }

    lastIndex = currentIndex + 1;
  }
}