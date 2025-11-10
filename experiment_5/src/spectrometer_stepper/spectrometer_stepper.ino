#include <Stepper.h>
#include "CSVPrinter.h"

const int laserPin = 3;
const int ldrPin = A0;
const int numSamples = 20;

// Stepper constants
const int SPR = 32;
const int GEAR_RED = 64;
const int TOTAL_STEPS = 1800;  // SPR * GEAR_RED;
const int STEP_INCREMENT = 8;

Stepper stepperMotor(SPR, 8, 10, 9, 11);

struct LDRStats {
    float mean;
    float stddev;
};

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
    // Use Bessel's correction for sample stddev
    float stddev = (numSamples > 1) ? sqrt(sumSq / (float)(numSamples - 1)) : 0;
    LDRStats stats = {mean, stddev};
    return stats;
}

void setup() {
    pinMode(laserPin, OUTPUT);
    digitalWrite(laserPin, HIGH); // Turn on laser
    stepperMotor.setSpeed(100); // Set speed to 100 RPM
    CSVPrinter::begin(9600);

    while (!Serial) {
        ; // Wait for Serial Monitor to open
    }

    CSVPrinter::printHeader("position,ldr_mean,ldr_stddev");
    delay(50); // Allow time for laser to stabilize
}

void loop() {
    static bool done = false;
    if (!done) {
        for (int step = 0; step <= TOTAL_STEPS; step += STEP_INCREMENT) {
            stepperMotor.step(STEP_INCREMENT); // Move stepper
            delay(50); // Allow time for motor to stabilize
            LDRStats stats = averageReadLDR(ldrPin, numSamples);
            CSVPrinter::printRow(step, stats.mean, stats.stddev);
            delay(50);
        }
        done = true;
        digitalWrite(laserPin, LOW); // Turn off laser
        stepperMotor.setSpeed(500); // Increase speed for return
        stepperMotor.step(-TOTAL_STEPS); // Return to start
    }
}