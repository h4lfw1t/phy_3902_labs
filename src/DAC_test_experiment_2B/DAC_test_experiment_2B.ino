#include <Wire.h>
#include <Adafruit_MCP4725.h>

// - Variables
bool hasRun = false;
float outputVoltage;
float measuredInputSignal;
float measuredInputVoltage;
unsigned long analogReadPIN = A0;

Adafruit_MCP4725 dac;

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
    Serial.println("Ouput Voltage     Measured Voltage");
    for (int i = 0; i < 51; i++) {
      int outputSignal = float_map(i, 0, 51, 0, 4095);
      dac.setVoltage(outputSignal, false);
      outputVoltage = i / 10.0;
      Serial.print(outputVoltage);

      delay(50);

      measuredInputSignal = analogRead(analogReadPIN);
      measuredInputVoltage = float_map(measuredInputSignal, 0, 1023, 0, 50) / 10.0;
      measuredInputVoltage = measuredInputVoltage;

      int space_count = 18 - String(outputVoltage).length();
      spacer(space_count);

      Serial.println(measuredInputVoltage);
      delay(50);
    }
    Serial.println("Finished");
    hasRun = true;
  }
}

float float_map(float value, float fromLow, float fromHigh, float toLow, float toHigh) {
  return toLow + ((value - fromLow) * (toHigh - toLow)) / (fromHigh - fromLow);
}

void spacer(int num) {
  for (int i = 0; i < num; i++) {
    Serial.print(" ");
  }
}
