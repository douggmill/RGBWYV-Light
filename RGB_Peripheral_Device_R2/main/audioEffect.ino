void setupAudioEffect() {
  pinMode(analogPin, INPUT);
  pinMode(strobePin, OUTPUT);
  pinMode(resetPin, OUTPUT);
  digitalWrite(resetPin, LOW);
  digitalWrite(strobePin, HIGH);
}

float mapADCToPercentage(float adcValue, float lowerThreshold, float upperThreshold) {
  float adcLowerThreshold = adcValueResolution * lowerThreshold;
  float percentage = 0.0;
  if (adcValue >= adcLowerThreshold) {
    float adcUpperTreshold = (upperThreshold * adcValueResolution) - adcLowerThreshold;
    if (adcUpperTreshold <= 0.0) {
      return 0.0;
    }
    adcValue -= adcLowerThreshold;
    percentage = (adcValue / adcUpperTreshold) * 100.0;
    percentage = constrain(percentage, 0.0, 100.0);
  }

  return percentage;
}

void audioEffect() {
  // Reset MSGEQ7
  digitalWrite(resetPin, HIGH);
  delayMicroseconds(1);
  digitalWrite(resetPin, LOW);

  // Reset sums and duty cycle values
  for (int i = 0; i < 5; i++) {
    multiplierSums[i] = 0.0;
    dutyCycleValues[i] = 0.0;
  }

  // Read 7 spectrum values and map them to percentages
  for (int i = 0; i < 7; i++) {
    digitalWrite(strobePin, LOW);
    delayMicroseconds(30);
    adcValue = analogRead(analogPin);
    spectrumValues[i] = mapADCToPercentage(adcValue, lowerThresholds[i], upperThresholds[i]);

    // Accumulate multiplier sums for normalization (read-only; do not mutate stored weights)
    multiplierSums[0] += redMultipliers[i];
    multiplierSums[1] += amberMultipliers[i];
    multiplierSums[2] += greenMultipliers[i];
    multiplierSums[3] += blueMultipliers[i];
    multiplierSums[4] += violetMultipliers[i];

    digitalWrite(strobePin, HIGH);
  }

  // Scale duty math only; leave redMultipliers[] etc. as the user-set source of truth
  float scales[5];
  for (int c = 0; c < 5; c++) {
    scales[c] = (multiplierSums[c] > 1.0) ? (1.0f / multiplierSums[c]) : 1.0f;
  }

  for (int i = 0; i < 7; i++) {
    dutyCycleValues[0] += spectrumValues[i] * redMultipliers[i] * scales[0];
    dutyCycleValues[1] += spectrumValues[i] * amberMultipliers[i] * scales[1];
    dutyCycleValues[2] += spectrumValues[i] * greenMultipliers[i] * scales[2];
    dutyCycleValues[3] += spectrumValues[i] * blueMultipliers[i] * scales[3];
    dutyCycleValues[4] += spectrumValues[i] * violetMultipliers[i] * scales[4];
  }

  dutyCycleValues[5] = 0.0;  // white stays off in audio mode
  writeFreqAndPWMtoPins();
}
