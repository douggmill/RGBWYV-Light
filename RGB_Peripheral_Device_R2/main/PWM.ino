void setupPWM() {
  for (int i = 0; i < NUM_OF_PINS; i++) {
    PWM_Instances[i] = new nRF52_PWM(PWM_Pins[i], frequency, dutyCycleOffValue);
    if (PWM_Instances[i]) {
      PWM_Instances[i]->setPWM(PWM_Pins[i], frequency, dutyCycleOffValue);
    }
  }
}

void writeFreqAndPWMtoPins() {
  for (int i = 0; i < NUM_OF_PINS; i++) {
    if (PWM_Instances[i]) {
      dutyCycleValues[i] = constrain(dutyCycleValues[i], 0.0, 99.9999);
      PWM_Instances[i]->setPWM(PWM_Pins[i], frequency, dutyCycleValues[i]);
    }
  }
}

void setPWMtoZero() {
  for (int i = 0; i < NUM_OF_PINS; i++) {
    dutyCycleValues[i] = dutyCycleOffValue;
    if (PWM_Instances[i]) {
      PWM_Instances[i]->setPWM(PWM_Pins[i], frequency, dutyCycleOffValue);
    }
  }
}
