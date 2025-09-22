#include <Wire.h>
#include <Adafruit_MCP4725.h>


/**
 * PHY 3902 Experiment 2C: DAC LED Characterization
 *
 * This sketch ramps a DAC output from 0V to 5V, measures voltages at three analog pins,
 * and prints results in CSV format for analysis. The code is modularized for clarity and maintainability.
 */

// --- Constants ---
const float RESISTOR = 218.3; // Ohms
const float DIODE_RESISTANCE = 0;  // Ohms
const uint8_t DAC_ADDR = 0x62;
const int DAC_STEPS = 51;
const float DAC_VOLTAGE_STEP = 0.1;
const int DAC_RESOLUTION = 4095;
const int ANALOG_READ_DELAY = 50;

// --- Globals ---
bool hasRun = false;
Adafruit_MCP4725 dac;

template <typename T>
void printSerialCSV(T value, bool eol = false) {
  if (eol) {
    Serial.println(value);
  } else {
    Serial.print(String(value) + ",");
  }
}

void setup() {
  Serial.begin(9600);
  dac.begin(0x62);
  for (int i = 0; i < 35; i++) {
    Serial.print("-");
  }
  Serial.println();
  Serial.println("DAC mounted to 0x62");
}


// --- DAC Control ---
void setDACVoltageByStep(int step) {
  int outputSignal = float_map(step, 0, 51, 0, 4095);
  dac.setVoltage(outputSignal, false);
}

// --- Data Acquisition ---
void acquireAndPrintData(int step) {
  float outputVoltage = step / 10.0;
  setDACVoltageByStep(step);
  delay(50);

  float signalA0 = readA0();
  float signalA1 = readA1();
  float signalA2 = readA2();

  Serial.print(String(outputVoltage) + ",");
  printSerialCSV(signalA0);
  printSerialCSV(signalA1);
  printSerialCSV(signalA2);
  printSerialCSV(signalA0 - signalA1);
  printSerialCSV(signalA1 - signalA2);
  printSerialCSV(((signalA0 - signalA1) / RESISTOR * 1000), true);
  delay(50);
}

void printHeader() {
  for (int i = 0; i < 35; i++) Serial.print("-");
  Serial.println();
  Serial.println("DAC mounted to 0x62");
  Serial.println("Outputting voltage series.");
  Serial.println("out,A0,A1,A2,A0-A1,A1-A2,current (mA)");
}

void loop() {
  if (!hasRun) {
    printHeader();
    for (int i = 0; i < 51; i++) {
      acquireAndPrintData(i);
    }
    Serial.println("Finished");
    hasRun = true;
  }
}

// - Helpers to read specific pins - 
float readA0() {
  return readAnalogToVoltage(A0);
}

float readA1() {
  return readAnalogToVoltage(A1);
}

float readA2() {
  return readAnalogToVoltage(A2);
}

/*
 * Read the 10-bit analog `pin` and output a float voltage 
 * representation between 0-5V
 */

// --- Utility Functions ---
/**
 * Map a float value from one range to another.
 */
float float_map(float value, float fromLow, float fromHigh, float toLow, float toHigh) {
  return toLow + ((value - fromLow) * (toHigh - toLow)) / (fromHigh - fromLow);
}

/**
 * Read the 10-bit analog `pin` and output a float voltage between 0-5V.
 */
float readAnalogToVoltage(uint8_t pin) {
  return float_map(analogRead(pin), 0, 1023, 0, 5.0);
}