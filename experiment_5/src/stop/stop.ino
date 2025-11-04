#include <Stepper.h>

Stepper stepperMotor(32, 8, 10, 9, 11);

void setup() {
    stepperMotor.setSpeed(500); // Set speed to 100 RPM
    stepperMotor.step(-2048); // Ensure starting at initial position
    delay(1000); // Don't do anything
}

void loop() {
    // Do nothing
}