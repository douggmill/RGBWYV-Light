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
    dutyCycleValues[i] = 0.0;  // Ensure duty cycles start at 0
  }

  // Read 7 spectrum values and map them to percentages
  for (int i = 0; i < 7; i++) {
    digitalWrite(strobePin, LOW);
    delayMicroseconds(30);
    adcValue = analogRead(analogPin);
    // bleuart.print(adcValue);
    spectrumValues[i] = mapADCToPercentage(adcValue, lowerThresholds[i], upperThresholds[i]);

    // Accumulate multiplier sums for normalization
    multiplierSums[0] += redMultipliers[i];
    multiplierSums[1] += amberMultipliers[i];
    multiplierSums[2] += greenMultipliers[i];
    multiplierSums[3] += blueMultipliers[i];
    multiplierSums[4] += violetMultipliers[i];

    digitalWrite(strobePin, HIGH);
  }


  adjustAllMultipliers();  // Normalize multipliers if needed


  for (int i = 0; i < 7; i++) {  // Calculate duty cycle values based on spectrum and normalized multipliers
    dutyCycleValues[0] += spectrumValues[i] * redMultipliers[i];
    dutyCycleValues[1] += spectrumValues[i] * amberMultipliers[i];
    dutyCycleValues[2] += spectrumValues[i] * greenMultipliers[i];
    dutyCycleValues[3] += spectrumValues[i] * blueMultipliers[i];
    dutyCycleValues[4] += spectrumValues[i] * violetMultipliers[i];
  }

  dutyCycleValues[5] = whiteValue;  // Assign white value if applicable
  writeFreqAndPWMtoPins();          // Write duty cycles to pins
}



void normalizeMultipliers(float* multipliers, float sum, int size) {
  if (sum > 1.0) {
    float inverse = 1.0 / sum;  // Precompute inverse for efficiency
    for (int i = 0; i < size; i++) {
      multipliers[i] *= inverse;
    }
  }
}



void adjustAllMultipliers() {
  normalizeMultipliers(redMultipliers, multiplierSums[0], 7);
  normalizeMultipliers(amberMultipliers, multiplierSums[1], 7);
  normalizeMultipliers(greenMultipliers, multiplierSums[2], 7);
  normalizeMultipliers(blueMultipliers, multiplierSums[3], 7);
  normalizeMultipliers(violetMultipliers, multiplierSums[4], 7);
}
