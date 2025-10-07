/* 
 *  Laser Properties - stepper movement + voltage measurement
 *  This code is a basic sketch that highlights how to move a stepper motor and make a voltage measurement. In this experiment, 
 *  you will have to modify this sketch to rotate the stepper motor in small increments and take a light intensity measurement at each 
 *  increment. FOR loops are useful for actuating motors in small increments. Remember that you need to calibrate the stepper motor so that 
 *  you know how many degrees you are rotating the stepper motor for a given number of "steps". Also, the light intensity measurement might
 *  be noisy, so calculating an average and uncertainties might be important!
 * 
 *  - Michel Godin for PHY3902
 */

#include <Stepper.h>      //library required to use the stepper motor functions


// Define Variables 
int laserPin = 3;     // We will use an output pin to power the laser. 
const int ldrPin = A0; // LDR analog input pin
const int increment = 1; // Number of steps per increment (smaller for more data points)
const int numSamples = 100; // Number of LDR samples to average per position

// Stepper Motor constants 
const int SPR = 32; 
const int GEAR_RED = 64; 
const int TOTAL_STEPS = SPR * GEAR_RED;  // Total number of steps for one full rotation of the stepper motor

// Create Instance of Stepper Class 
// Specify Pins used for motor coils 
// Pins are 8, 9, 10, 11 
// Connected to ULN2003 Motor Driver IN1, IN2, IN3, IN4
// Pins entered in sequence 1-3-2-4 for proper stepper sequencing 

Stepper stepperMotor(SPR, 8, 10, 9, 11);

/**
 * @brief Prints a value in CSV format to the Serial output.
 *
 * @tparam T The type of the value to print.
 * @param value The value to print.
 * @param eol If true, prints a newline after the value; otherwise, prints a comma.
 */
template <typename T>
void printSerialCSV(T value, bool eol = false, int precision = 4) {
  if (eol) {
    Serial.println((float)value, precision);
  } else {
    Serial.print((float)value, precision);
    Serial.print(",");
  }
}

/**
 * @brief Prints a full CSV row of the experiment data to Serial.
 * @param step The current step of the stepper motor.
 * @param adcValue The ADC value read from the sensor.
 * @param adcError The error associated with the ADC reading.
 */
void printDataCSVRow(
  int step, float adcMean, float adcStddev
) {
  printSerialCSV(step);
  printSerialCSV(adcMean);
  printSerialCSV(adcStddev, true);
}

/**
 * @brief Holds the mean and standard deviation of LDR readings.
 */
struct LDRStats {
  float mean;
  float stddev;
};

/**
 * @brief Averages multiple readings from an LDR connected to the specified analog pin.
 * @param pin The analog pin where the LDR is connected.
 * @param numSamples The number of samples to average.
 * @return LDRStats struct containing mean and standard deviation.
 */
LDRStats averageReadLDR(int pin, int numSamples) {
  float total = 0;
  float values[20]; // max 20 samples for memory safety
  if (numSamples > 20) numSamples = 20;
  for (int i = 0; i < numSamples; i++) {
    values[i] = analogRead(pin);
    total += values[i];
    delay(10); // Small delay to allow ADC to stabilize
  }
  float mean = total / (float)numSamples;
  float sumSq = 0;
  for (int i = 0; i < numSamples; i++) {
    sumSq += (values[i] - mean) * (values[i] - mean);
  }
  float stddev = sqrt(sumSq / (float)numSamples);
  LDRStats stats = {mean, stddev};
  return stats;
}

void setup() {
  pinMode(laserPin, OUTPUT);
  digitalWrite(laserPin, HIGH); // Turn on the laser
  stepperMotor.setSpeed(50);   // Slow speed for accuracy
  Serial.begin(9600);
  Serial.println("step,adc_mean,adc_stddev"); // CSV header
}

void loop() {
  static bool done = false;
  if (!done) {
    digitalWrite(laserPin, HIGH); // Laser ON
    for (int step = 0; step <= TOTAL_STEPS; step += increment) {
      stepperMotor.step(increment); // Move stepper
      LDRStats stats = averageReadLDR(ldrPin, numSamples); // Average LDR
      printDataCSVRow(step, stats.mean, stats.stddev); // Print CSV row
      delay(20); // Stability delay
    }
    digitalWrite(laserPin, LOW); // Laser OFF
    done = true;
  }
}
