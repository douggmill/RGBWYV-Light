void setupInternalFS() {

  if (!InternalFS.begin()) {
    bleuart.print("Failed to init FS");
    // while (1) { delay(10); }

  } else {
    bleuart.print("FS initialized");
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
  readValuesFromFS();
  parseCSVtoADCandEffect();
}



void saveValuesToFS() {

  eraseValuesFile();
  file = InternalFS.open("data.txt", FILE_O_WRITE);

  if (!file) {
    bleuart.print("Failed to open file!");
    return;
  }

  bleuart.print("Writing to file...");
  file.println(allValuesCSV);  // Write the String
  file.close();

  bleuart.print("Write complete.");
}


void readValuesFromFS() {
  allValuesCSV = "";  // Clear any previous value

  file = InternalFS.open("data.txt", FILE_O_READ);
  if (file) {
    bleuart.print("Reading file contents:");
    while (file.available()) {
      char c = file.read();
      allValuesCSV += c;  // Append each character to the String
    }
    file.close();

    // Optional: Show the loaded string
    print_inChunks();
  } else {
    bleuart.print("Failed to read FS!");
  }
}



void buildAllValuesCSV() {
  allValuesCSV = "";  // Clear existing content

  for (int i = 0; i < 7; i++) {
    allValuesCSV += String((int)(redMultipliers[i] * 1000)) + ",";
  }
  for (int i = 0; i < 7; i++) {
    allValuesCSV += String((int)(amberMultipliers[i] * 1000)) + ",";
  }
  for (int i = 0; i < 7; i++) {
    allValuesCSV += String((int)(greenMultipliers[i] * 1000)) + ",";
  }
  for (int i = 0; i < 7; i++) {
    allValuesCSV += String((int)(blueMultipliers[i] * 1000)) + ",";
  }
  for (int i = 0; i < 7; i++) {
    allValuesCSV += String((int)(violetMultipliers[i] * 1000)) + ",";
  }
  for (int i = 0; i < 7; i++) {
    allValuesCSV += String((int)(upperThresholds[i] * 1000)) + ",";
  }
  for (int i = 0; i < 7; i++) {
    allValuesCSV += String((int)(lowerThresholds[i] * 1000)) + ",";
  }

  for (int i = 0; i < 6; i++) {
    allValuesCSV += String((int)(RYGBVW_Values[i] * 10)) + ",";
  }
  allValuesCSV += String((int)(frequency / 10)) + ",";
  allValuesCSV += String((int)(adc[56] * 1000)) + ",";
  allValuesCSV += String((int)(adc[57] * 1000)) + ",";
  allValuesCSV += String((int)(adc[58] * 1000)) + ",";
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
  whiteValue = adc[54] * 100.0;  // can be manually addjusted in any effect mode
  frequency = adc[55] * 10000.00;
}



void eraseValuesFile() {
  if (InternalFS.remove("data.txt")) {
    bleuart.print("File deleted.");
  } else {
    bleuart.print("Failed to delete file.");
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