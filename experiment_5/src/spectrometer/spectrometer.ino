# include <Servo.h>
# include "CSVPrinter.h"

// Define variables
int pos = 0;
bool hasRun = false;
Servo myServo;

// Define constants
const int SERVO_PIN = 9; // Pin connected to the servo signal wire
const int LASER_PIN = 3; // Pin connected to the laser
const int LDR_PIN = A0;  // Pin connected to the LDR
const int NUM_SAMPLES = 100; // Number of samples to average for LDR reading

// Servo stage constants
// Servo stage moves 5 cm per full rotation (gear ratio 16:16)
const float STAGE_LENGTH = 0.05;  // Length per full rotation in meters

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
    CSVPrinter::begin(9600);
    myServo.attach(SERVO_PIN);
    pinMode(LASER_PIN, OUTPUT);
    digitalWrite(LASER_PIN, HIGH); // Turn on laser
    myServo.write(0); // Initialize servo position
    delay(1000); // Wait for servo to reach position

    // Print CSV header
    CSVPrinter::printHeader("position,ldr_mean,ldr_stddev");
}

void loop() {
    if (hasRun) {
        return; // Only run once
    }
    for (pos = 0; pos <= 360; pos += 1) {
        myServo.write(pos);
        delay(50); // Wait for servo to reach position

        // Take LDR reading

        LDRStats stats = averageReadLDR(LDR_PIN, NUM_SAMPLES);
        float ldrValue = stats.mean; // Use mean value for CSV
        float ldrStdDev = stats.stddev; // Use standard deviation for CSV
        float positionMeters = (pos / 360.0) * STAGE_LENGTH; // Convert to meters

        // Print CSV row
        CSVPrinter::printRow(positionMeters, ldrValue, ldrStdDev);

        delay(100);
    }
    for (pos = 360; pos >= 0; pos -= 1) {
        myServo.write(pos);
        delay(50); // Wait for servo to reach position

        // Take LDR reading
        LDRStats stats = averageReadLDR(LDR_PIN, NUM_SAMPLES);
        float ldrValue = stats.mean; // Use mean value for CSV
        float ldrStdDev = stats.stddev; // Use standard deviation for CSV
        float positionMeters = (pos / 360.0) * STAGE_LENGTH; // Convert to meters

        // Print CSV row
        CSVPrinter::printRow(positionMeters, ldrValue, ldrStdDev);

        delay(100);
    }
    // hasRun = true;
}