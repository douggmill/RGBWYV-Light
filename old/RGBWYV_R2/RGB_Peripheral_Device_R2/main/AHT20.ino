void setupAHT20TempSensor() {

  if (!aht.begin()) {
    statusI2C_1 = 0;
    //Serial.println(statusI2C_1);
  } else {
    statusI2C_1 = 1;
    //Serial.println(statusI2C_1);
  }
}

void getTempForFan() {

  if (statusI2C_1 == 1) {

    sensors_event_t humidity, temp;
     aht.getEvent(&humidity, &temp);
    // snprintf(buffer, sizeof(buffer), "Int: %d, Float: %.2f", myInt, myFloat); // concat int and float example

    if (temp.temperature >= fanOnTemp && statusI2C_2 == 1 && fanState == 0) {
      fanState = 1;
      pcf.digitalWrite(2, fanState);
      snprintf(output, BUFFER_SIZE2, "FanOn %.2fdegC", temp.temperature);
      bleuart.print(output);
      memset(output, 0, BUFFER_SIZE2);


    } else if (temp.temperature >= fanOnTemp && statusI2C_2 == 0 && fanState == 0) {

      snprintf(output, BUFFER_SIZE2, "FanError %.2fdegC", temp.temperature);
      bleuart.print(output);
      memset(output, 0, BUFFER_SIZE2);

    } else if (temp.temperature <= fanOffTemp && statusI2C_2 == 1 && fanState == 1) {
      fanState = 0;
      pcf.digitalWrite(2, fanState);
      snprintf(output, BUFFER_SIZE2, "FanOff %.2fdegC", temp.temperature);
      bleuart.print(output);
      memset(output, 0, BUFFER_SIZE2);


    } else {
      snprintf(output, BUFFER_SIZE2, "TempCheck %.2fdegC", temp.temperature);
      bleuart.print(output);
      memset(output, 0, BUFFER_SIZE2);
    }

    bleuart.print(output);
  }
}