////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////Perpheral Device/////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////
// BEFORE including <nRF52_PWM.h>
#ifdef _PWM_LOGLEVEL_
#undef _PWM_LOGLEVEL_
#endif
#define _PWM_LOGLEVEL_ 0
#include <nRF52_PWM.h>
#include <bluefruit.h>
#include <Adafruit_PCF8574.h>
#include <Adafruit_AHTX0.h>
#include <Adafruit_LittleFS.h>
#include <InternalFileSystem.h>

//---------Programable Button--------------//



#define _PWM_LOGLEVEL_ 0
#define USING_TIMER false  // Select false to use PWM

#define analogPin A0
#define resetPin 1
#define strobePin 10

#define NUM_OF_PINS 6

#define GREEN_PIN 2
#define RED_PIN 7
#define BLUE_PIN 8

#define AMBER_PIN 9
#define VIOLET_PIN 3
#define WHITE_PIN 6

float spectrumValues[7];  // Array to hold amplitude values for each band
float adcValue = 0.0;
float adcValueResolution = 1023.0;  // 10bit for nRF52840 Ainputs
float percentage = 0.0;

float adc[59] = {
  1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,   // redMultipliers
  0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,   // amberMultipliers
  0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0,   // greenMultipliers
  0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0,   // blueMultipliers
  0.0, 0.0, 0.0, 0.5, 0.5, 0.0, 0.0,   // violetMultipliers
  1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,   // upperTresholds
  0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,   // lowerThresholds
  0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.50,  // manualValues R,Y,G,B,V,W,freq
  0.0, 0.0, 0.0                        // rainbow (wave) effect
};

float redMultipliers[7] = { adc[0], adc[1], adc[2], adc[3], adc[4], adc[5], adc[6] };
float amberMultipliers[7] = { adc[7], adc[8], adc[9], adc[10], adc[11], adc[12], adc[13] };
float greenMultipliers[7] = { adc[14], adc[15], adc[16], adc[17], adc[18], adc[19], adc[20] };
float blueMultipliers[7] = { adc[21], adc[22], adc[23], adc[24], adc[25], adc[26], adc[27] };
float violetMultipliers[7] = { adc[28], adc[29], adc[30], adc[31], adc[32], adc[33], adc[34] };
float upperThresholds[7] = { adc[35], adc[36], adc[37], adc[38], adc[39], adc[40], adc[41] };
float lowerThresholds[7] = { adc[42], adc[43], adc[44], adc[45], adc[46], adc[47], adc[48] };
float RYGBVW_Values[6] = { adc[49], adc[50], adc[51], adc[52], adc[53], adc[54] };  // used for manualControl (adc[chan]*100.0)
float whiteValue = adc[54] * 100.0;                                                 // can be manually addjusted in any effect mode
float frequency = adc[55] * 10000.00;                                               // 10kHz max, initial value set to 1khz for now
float multiplierSums[5] = { 0.0, 0.0, 0.0, 0.0, 0.0 };

float dutyCycleValues[NUM_OF_PINS] = { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 };                           // Ensure it's initialized properly
int PWM_Pins[NUM_OF_PINS] = { RED_PIN, AMBER_PIN, GREEN_PIN, BLUE_PIN, VIOLET_PIN, WHITE_PIN };  // Array of pins for PWM
int effectModes = 1;                                                                             // 0 == wave, 1 == music, 2 == manual              // 0 = manualControl, 1 = audioEffect, else = off

String allValuesCSV = "";

//-----------------------------------rainbow effect-------------------------------------------//

int phaseIndexRain = 0;                      // Initial phase index for rav_wav
float colorIndexRain = 0.0;                  // Variable to track color transition within each phase
unsigned long previousMillisEffectRain = 0;  // Common previousMillis for all phases
unsigned long intervalEffectRain = 0;        // Default interval, will be updated dynamically

//-----------------------------------Constants-------------------------------------------//
const int BUFFER_SIZE = 256;  // Adjust size as needed
const int BUFFER_SIZE2 = 32;  // Adjust size as needed
const char Manufacturer[] = "Doug's Garage";
const char Model[] = "LED Device 001";
const float dutyCycleOffValue = 0.0;

//---------------------------------Command Buffers----------------------------------------//

char input[BUFFER_SIZE];    // serial buffer
char output[BUFFER_SIZE2];  // ble output buffer
bool BLEisConnected = false;

//--------------------------------------TempFan----------------------------------------//

float fanOnTemp = 35.00;  // in degC
float fanOffTemp = 32.00;
bool fanState = 0;
unsigned long temp_Sample_Delay = 30000;  // 30 sec
unsigned long previousMillis = 0;
bool statusI2C_1 = 0;
bool statusI2C_2 = 0;

//--------------------------------initialize objects---------------------------------//
using namespace Adafruit_LittleFS_Namespace;
File file(InternalFS);
nRF52_PWM* PWM_Instances[NUM_OF_PINS];
BLEUart bleuart;
BLEDis bledis;
Adafruit_AHTX0 aht;
Adafruit_PCF8574 pcf;

//--------------------------------function prototypes---------------------------------//

void handleComms();
void setupAudioEffect();
void setupPWM();
void setupBLE_Peripheral();
void audioEffect();
void setupAHT20TempSensor();
void setupPCF8574();
void timedFunctions();
void RainbowEffect(float value1, float value2, float value3);
// void setupSerial();
void setupInternalFS();

void setup() {

  // analogReadResolution(12);
  // setupSerial();
  setupAudioEffect();
  setupPWM();
  setupPCF8574();
  setupAHT20TempSensor();
  setupInternalFS();

  /////////////////////////// Put BLE Setup Last!!! ////////////////////////////////////
  setupBLE_Peripheral();

  if (effectModes == 2) {
    writeManual();
  }
}

void loop() {
  if (BLEisConnected && bleuart.available()) {
    handleComms();  // Run only when communication is received
  }
  if (effectModes == 0) {
    Rainbow_Classic(adc[56], adc[57], adc[58]);
  }
  if (effectModes == 1) {
    audioEffect();
  }
  if (effectModes == 3) {
    RetroEffect(adc[56], adc[57], adc[58]);
  }

  timedFunctions();
}
