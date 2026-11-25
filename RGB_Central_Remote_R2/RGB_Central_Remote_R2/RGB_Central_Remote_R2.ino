////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////Central Device///////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////


#include <bluefruit.h>
// #include <Adafruit_LittleFS.h>
// #include <InternalFileSystem.h>


const char deviceName[] = "LED Console 001";
const char Manufacturer[] = "Doug's Garage";
const int BUFFER_SIZE = 128;
char USB_UART[BUFFER_SIZE];   // serial buffer

char modelBuffer[BUFFER_SIZE];
char manufacturerBuffer[BUFFER_SIZE];
int inputIndex = 0;
bool infoAvailable = false;

const char helpMenu[] = "--------------------------------------------------------\n\r"
                        "|                   Central Commands                   |\n\r"
                        "--------------------------------------------------------\n\r\n\r"
                        "help = list commands stored in the central device.\n\r"
                        "info = get peripheral ID and manufacturer.\n\r"
                        "*idn = get central ID.\n\r\n\r"
                        "--------------------------------------------------------\n\r"
                        "|                 Peripheral Commands                  |\n\r"
                        "--------------------------------------------------------\n\r\n\r"
                        "temp = print internal temp in celsius.\n\r"
                        "fan0 = turn fan off.\n\r"
                        "fan1 = turn fan on.\n\r"
                        "err? = print I2C status, 0 = bad, 1 = good.\n\r"
                        "val? = print live RAM values as a comma-separated list.\n\r"
                        "save = save current adc[] values and mode to the file system.\n\r"
                        "read = print saved file values and reload them into RAM.\n\r"
                        "dele = delete the saved values file.\n\r"
                        "mode,0 = classic RGB rainbow (R-G-B swell).\n\r"
                        "mode,1 = audio effect (MSGEQ7).\n\r"
                        "mode,2 = manual color mixer.\n\r"
                        "mode,3 = retro color swells (R-G-Violet).\n\r"
                        "adc#,VALUE = set parameter; VALUE is 0-1000 (1000 = 1.0).\n\r\n\r"

                        "Audio mode 1 only (7 bands: 63Hz, 160Hz, 400Hz, 1kHz, 2.5kHz, 6.25kHz, 16kHz):\n\r"
                        "adc 0-6   = red mixer for each band.\n\r"
                        "adc 7-13  = amber mixer for each band.\n\r"
                        "adc 14-20 = green mixer for each band.\n\r"
                        "adc 21-27 = blue mixer for each band.\n\r"
                        "adc 28-34 = violet mixer for each band.\n\r"
                        "adc 35-41 = upper thresholds for each band.\n\r"
                        "adc 42-48 = lower thresholds for each band.\n\r\n\r"

                        "Manual mode 2 only:\n\r"
                        "adc49 = red LED.\n\r"
                        "adc50 = amber LED.\n\r"
                        "adc51 = green LED.\n\r"
                        "adc52 = blue LED.\n\r"
                        "adc53 = violet LED.\n\r\n\r"

                        "Classic RGB (mode 0) and retro swells (mode 3):\n\r"
                        "adc56 = velocity / speed.\n\r"
                        "adc57 = pastel (white level).\n\r"
                        "adc58 = brightness (color amplitude).\n\r\n\r"

                        "Always available:\n\r"
                        "adc54 = white LED.\n\r"
                        "adc55 = PWM frequency, 10 kHz max (1000 = 10 kHz). Applied in manual and audio modes.\n\r\n\r";
                        

//------------------------------function prototypes-------------------------------//

void handleComms();
void setupBLE_Central();
void setupSerial();
// void setupInternalFS();
void checkID();

//--------------------------------initialize objects---------------------------------//
BLEClientDis clientDis;    // device information client
BLEClientUart clientUart;  // bleuart client

void setup() {

  setupSerial();

  // setupInternalFS();

  setupBLE_Central();

  Serial.print(Manufacturer);
  Serial.println(", ");
  Serial.print(deviceName);
  Serial.println(" initialized and scanning");
}



void loop() {
  //if (Bluefruit.Central.connected() && clientUart.discovered()) {  // Only perform when Peripheral is connected
  //  timedFunctions();
  //}
  handleComms();
}
