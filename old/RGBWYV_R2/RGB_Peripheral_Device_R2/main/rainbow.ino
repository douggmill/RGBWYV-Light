static inline void writeRGBW_generic(const int rgbIdx[3], int whiteIdx) {
  for (int k = 0; k < 3; k++) {
    int i = rgbIdx[k];
    if (!PWM_Instances[i]) continue;
    float pct = dutyCycleValues[i];
    if (pct < 0) pct = 0; if (pct > 100) pct = 100;
    uint16_t counts = (uint16_t) lroundf((pct * 65535.0f) / 100.0f);
    PWM_Instances[i]->setPWM_manual(PWM_Pins[i], counts);
  }
  if (whiteIdx >= 0 && PWM_Instances[whiteIdx]) {
    float wpct = dutyCycleValues[whiteIdx];
    if (wpct < 0) wpct = 0; if (wpct > 100) wpct = 100;
    uint16_t wcounts = (uint16_t) lroundf((wpct * 65535.0f) / 100.0f);
    PWM_Instances[whiteIdx]->setPWM_manual(PWM_Pins[whiteIdx], wcounts);
  }
}

static inline void writeClassicEffect() { const int idx[3] = {0,2,3}; writeRGBW_generic(idx, 5); }
static inline void writeRetroEffect()   { const int idx[3] = {0,2,4}; writeRGBW_generic(idx, 5); }




static inline float mapFloat(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}


// Signature matches your main: Rainbow_Classic(adc[56], adc[57], adc[58])
void Rainbow_Classic(float speed_cps, float whiteLevel, float rgbBase)
{
  unsigned long currentMillisEffect = millis();

  // constant frame interval for smooth fades at any speed
  const float FRAME_MS = 10.0f;   // ~100 FPS (try 8..12 if you want)
  intervalEffectRain = FRAME_MS;

  // clamp speed for step math
  float spd = speed_cps;
  if (spd < 0.0f)   spd = 0.0f;
  if (spd > 1.0f)   spd = 1.0f;
  if (spd < 0.001f) spd = 0.001f;  // avoid zero


  // Inputs as percents for the maps/writes
  float maxRGB = rgbBase   * 100.0f;  // amplitude for the two active channels
  float whiteP = whiteLevel * 100.0f; // manual white

  // Always write White from the 2nd parameter (manual)
  dutyCycleValues[5] = whiteP;

  // Update only on interval tick
  if (currentMillisEffect - previousMillisEffectRain >= intervalEffectRain) {
    previousMillisEffectRain = currentMillisEffect;

    float step = 0.3f * intervalEffectRain * spd;   // colorIndexRain is 0..100 per phase
            
    switch (phaseIndexRain) {
      case 0: { // Red -> Green (Blue OFF)
        dutyCycleValues[0] = mapFloat(colorIndexRain, 0, 100, maxRGB, 0);      // R down
        dutyCycleValues[2] = mapFloat(colorIndexRain, 0, 100, 0, maxRGB);  // G up
        dutyCycleValues[3] = 0;                                                // B off
        writeClassicEffect();

        colorIndexRain += step;
        if (colorIndexRain > 100.0f) { colorIndexRain = 0.0f; phaseIndexRain = 1; }
      } break;

      case 1: { // Green -> Blue (Red OFF)
        dutyCycleValues[2] = mapFloat(colorIndexRain, 0, 100, maxRGB, 0);      // G down
        dutyCycleValues[3] = mapFloat(colorIndexRain, 0, 100, 0,maxRGB);  // B up
        dutyCycleValues[0] = 0;                                                // R off
        writeClassicEffect();

        colorIndexRain += step;
        if (colorIndexRain > 100.0f) { colorIndexRain = 0.0f; phaseIndexRain = 2; }
      } break;

      case 2: { // Blue -> Red (Green OFF)
        dutyCycleValues[3] = mapFloat(colorIndexRain, 0, 100, maxRGB, 0);      // B down
        dutyCycleValues[0] = mapFloat(colorIndexRain, 0, 100, 0,     maxRGB);  // R up
        dutyCycleValues[2] = 0;                                                // G off
        writeClassicEffect();

        colorIndexRain += step;
        if (colorIndexRain > 100.0f) { colorIndexRain = 0.0f; phaseIndexRain = 0; }
      } break;

      default:
        phaseIndexRain = 0;
        colorIndexRain = 0;
        dutyCycleValues[0] = maxRGB;
        dutyCycleValues[2] = 0;
        dutyCycleValues[3] = 0;
        writeClassicEffect();
        break;
    }
  }
}




void RetroEffect(float speed_cps, float whiteLevel, float rgbBase)
{
  const unsigned long now = millis();

  // ---- Constant frame rate ----
  const float FRAME_MS = 10.0f;        // ~100 FPS
  intervalEffectRain = FRAME_MS;

  // Clamp speed (allow true stop at 0)
  float spd = speed_cps;
  if (spd < 0.0f) spd = 0.0f;
  if (spd > 1.0f) spd = 1.0f;

  // Per-tick progress; each phase spans 0..100
  float step = 0.3f * intervalEffectRain * spd;

  // ---- Amplitudes (percent) ----
  const float VvioMax = rgbBase * 100.0f;     // Violet full-scale
  float RGcap = VvioMax * 0.10f;              // R/G capped to 10% of Violet
  if (RGcap < 0) RGcap = 0;

  // White passthrough; Blue OFF
  dutyCycleValues[5] = whiteLevel * 100.0f;
  dutyCycleValues[3] = 0.0f;                  // BLUE OFF

  // ---- One-time seed: start at Red @ peak ----
  static bool retroInit = false;
  if (!retroInit) {
    retroInit = true;
    phaseIndexRain = 0;            // 0: R→G
    colorIndexRain = 0.0f;         // at top of Red
    previousMillisEffectRain = now;

    dutyCycleValues[0] = RGcap;    // Red peak (10% of Violet max)
    dutyCycleValues[2] = 0.0f;     // Green off
    dutyCycleValues[4] = 0.0f;     // Violet off
    writeRetroEffect();
    return;                        // don’t advance on first frame
  }

  if (now - previousMillisEffectRain >= intervalEffectRain) {
    previousMillisEffectRain = now;

    // advance WITH carry-over (no wobble at boundaries)
    float next = colorIndexRain + step;
    if (next >= 100.0f) {
      colorIndexRain = next - 100.0f;
      phaseIndexRain = (phaseIndexRain + 1) % 3;
    } else {
      colorIndexRain = next;
    }

    // Common progress 0..1
    const float t  = colorIndexRain * 0.01f;

    // --- Option B: ease Violet phases so it doesn't "hang" near max ---
    // exponent < 1.0 => rises/falls faster near the top
    const float V_EASE = 0.85f;    // try 0.80..0.90
    const float tV  = powf(t, V_EASE);        // use for V going up
    const float tVd = powf(t, V_EASE);        // use for V going down

    switch (phaseIndexRain) {
      case 0: { // R -> G (Violet OFF)
        // linear crossfade between R and G; V stays 0
        dutyCycleValues[0] = RGcap * (1.0f - t);   // R down
        dutyCycleValues[2] = RGcap * t;           // G up
        dutyCycleValues[4] = 0.0f;                // V off
      } break;

      case 1: { // G -> Violet (Red OFF)
        dutyCycleValues[2] = RGcap   * (1.0f - t);   // G down (linear)
        dutyCycleValues[4] = VvioMax * tV;           // V up (eased → reaches high sooner)
        dutyCycleValues[0] = 0.0f;                   // R off
      } break;

      case 2: { // Violet -> Red (Green OFF)
        dutyCycleValues[4] = VvioMax * (1.0f - tVd); // V down (eased → leaves peak faster)
        dutyCycleValues[0] = RGcap   * t;            // R up (linear)
        dutyCycleValues[2] = 0.0f;                   // G off
      } break;
    }

    writeRetroEffect();   // R=0, G=2, Violet=4, White=5
  }
}

