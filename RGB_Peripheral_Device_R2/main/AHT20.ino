void setupAHT20TempSensor() {

  if (!aht.begin()) {
    statusI2C_1 = 0;
  } else {
    statusI2C_1 = 1;
  }
}

void getTempForFan() {

  if (statusI2C_1 != 1) {
    return;
  }

  sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);
  static bool fanErrorReported = false;

  if (temp.temperature >= fanOnTemp && statusI2C_2 == 1 && fanState == 0) {
    fanState = 1;
    fanErrorReported = false;
    pcf.digitalWrite(2, fanState);
    snprintf(output, BUFFER_SIZE2, "FanOn %.2fdegC", temp.temperature);
    bleuart.println(output);
    memset(output, 0, BUFFER_SIZE2);

  } else if (temp.temperature >= fanOnTemp && statusI2C_2 == 0 && fanState == 0) {
    if (!fanErrorReported) {
      snprintf(output, BUFFER_SIZE2, "FanError %.2fdegC", temp.temperature);
      bleuart.println(output);
      memset(output, 0, BUFFER_SIZE2);
      fanErrorReported = true;
    }

  } else if (temp.temperature <= fanOffTemp && statusI2C_2 == 1 && fanState == 1) {
    fanState = 0;
    fanErrorReported = false;
    pcf.digitalWrite(2, fanState);
    snprintf(output, BUFFER_SIZE2, "FanOff %.2fdegC", temp.temperature);
    bleuart.println(output);
    memset(output, 0, BUFFER_SIZE2);

  } else if (temp.temperature < fanOnTemp) {
    fanErrorReported = false;
  }
  // No periodic TempCheck spam, and no trailing empty bleuart.print.
}
