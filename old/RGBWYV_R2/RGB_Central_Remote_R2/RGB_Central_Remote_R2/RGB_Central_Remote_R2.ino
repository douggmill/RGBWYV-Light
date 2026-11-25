////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////Central Device///////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////


#include <bluefruit.h>
// #include <Adafruit_LittleFS.h>
// #include <InternalFileSystem.h>


const char deviceName[] = "LED Console 001";
const char Manufacturer[] = "Doug's Garage";
const int BUFFER_SIZE = 16;
char USB_UART[BUFFER_SIZE];   // serial buffer

char modelBuffer[BUFFER_SIZE];
char manufacturerBuffer[BUFFER_SIZE];
int inputIndex = 0;
bool infoAvailable = false;

const char helpMenu[] = "--------------------------------------------------------\n\r"
                        "|                   Central Commands                   |\n\r"
                        "--------------------------------------------------------\n\r\n\r"
                        "help = list stored in central device.\n\r"
                        "info = get peripheral ID and manufacturer.\n\r"
                        "*idn = get central ID and manufacturer.\n\r\n\r"
                        "--------------------------------------------------------\n\r"
                        "|                 Peripheral Commands                  |\n\r"
                        "--------------------------------------------------------\n\r\n\r"
                        "temp = print internal temp in celcius.\n\r"
                        "fan0 = turn fan off.\n\r"
                        "fan1 = turn fan on.\n\r"
                        "err? = prints i2c errors, 0 = bad, 1 = good.\n\r"
                        "val? = sends all current variables as a comma serperated value.\n\r"
                        "save = saves all current variables to File System.\n\r"
                        "read = directly from file.\n\r"
                        "mode,0 = swell (rainbow) effect mode button.\n\r"
                        "mode,1 = audio effect mode button.\n\r"
                        "mode,2 = manual mode button.\n\r"
                        "adc#,0.00 = commands from slider values 0.00-1.00.\n\r\n\r"

                        "The following values are active durring audio mode 1 only.\n\r"
                        "Each controls a group of seperate bands:\n\r"
                        "63Hz, 160Hz, 400Hz, 1kHz, 2.5kHz, 6.25kHz, 16kHz.\n\r"
                        "adc# 0-6 = red audio mixer for each band.\n\r"
                        "adc# 7-13 = amber audio mixer for each band.\n\r"
                        "adc# 14-20 = green audio mixer for each band.\n\r"
                        "adc# 21-27 = blue audio mixer for each band.\n\r"
                        "adc# 28-34 = violet audio mixer for each band.\n\r"
                        "adc# 35-41 = upper thresholds for each band.\n\r"
                        "adc# 42-48 = lower thresholds for each band.\n\r\n\r"

                        "The following values are active durring manual mode 2 only.\n\r"
                        "adc49 = red LED.\n\r"
                        "adc50 = amber LED.\n\r"
                        "adc51 = green LED.\n\r"
                        "adc52 = blue LED.\n\r"
                        "adc53 = violet LED.\n\r\n\r"

                        "The following values are active durring swell effect mode 0 only.\n\r"
                        "adc49 = Effect timing.\n\r"
                        "adc50 = upper effect limit.\n\r"
                        "adc51 = lower effect limit.\n\r\n\r"

                        "The following values are always active.\n\r"
                        "adc54 = white LED.\n\r"
                        "adc55 = PWM freq 10kHz max.\n\r\n\r";
                        

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
