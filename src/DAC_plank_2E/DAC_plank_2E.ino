#include <Wire.h>
#include <Adafruit_MCP4725.h>

// - Variables
bool hasRun = false;
float outputVoltage;
float measuredInputVoltage;
float const RESISTOR = 218.3; // Ohms
float const DIODE_RESISTANCE = 0;  // Ohms

Adafruit_MCP4725 dac;

// - Prototypes - 
template <typename T>
void printSerialCSV(T value, bool eol = false);

void setup() {
    Serial.begin(9600);
    dac.begin(0x62);
    for (int i = 0; i < 35; i++) {
        Serial.print("-");
    }
    Serial.println();
    Serial.println("DAC mounted to 0x62");
}

void loop() {
    if (not hasRun) {
        Serial.println("Outputting voltage series.");
        Serial.println("out,A0,A1,A2,A0-A1,A1-A2,current");
        for (int i = 0; i < 51; i++) {
        // Ramp voltage from 0V to 5V with a 0.1 step
        int outputSignal = float_map(i, 0, 51, 0, 4095);
        dac.setVoltage(outputSignal, false);
        outputVoltage = i / 10.0;
        Serial.print(String(outputVoltage) + ",");

        delay(50);

        float signalA0 = readA0();
        float signalA1 = readA1();
        float signalA2 = readA2();

        printSerialCSV(signalA0);
        printSerialCSV(signalA1);
        printSerialCSV(signalA2);
        printSerialCSV(signalA0 - signalA1);
        printSerialCSV(signalA1 - signalA2);
        printSerialCSV(((signalA0 - signalA1) / RESISTOR), true);

        delay(50);
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
float readAnalogToVoltage(unsigned long pin) {
    return float_map(analogRead(pin), 0, 1023, 0, 50) / 10.0;
}

// Custom map function to work with floats instead of integers
float float_map(float value, float fromLow, float fromHigh, float toLow, float toHigh) {
    return toLow + ((value - fromLow) * (toHigh - toLow)) / (fromHigh - fromLow);
}

template <typename T>
void printSerialCSV(T value, bool eol = false) {
    if (eol) {
        Serial.println(value);
    } else {
        Serial.print(String(value) + ",");
    }
}
