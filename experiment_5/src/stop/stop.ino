#include <Stepper.h>

Stepper stepperMotor(32, 8, 10, 9, 11);

void setup() {
    // stepperMotor.setSpeed(500); // Set speed to 100 RPM
    // stepperMotor.step(-1800); // Ensure starting at initial position
    pinMode(3, OUTPUT);
    digitalWrite(3, HIGH); // Turn on laser
    delay(1000); // Don't do anything
}

void loop() {
    // Do nothing
}