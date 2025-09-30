// STEPPER.ino
// The stepper.h library must be added here in order to use the stepper motor functions below. This library is built-in to Arduino by default.
#include <Stepper.h>

// Defining some Stepper Motor configuration parameters 
const float SPR = 32; // This would need to change depending on the stepper motor used.

// Create Instance of Stepper Class 
// Specify Pins used for motor coils 
// Pins are 8, 9, 10, 11 
// Connected to ULN2003 Motor Driver IN1, IN2, IN3, IN4
// Pins entered in sequence 1-3-2-4 for proper stepper sequencing 

Stepper stepperMotor(SPR, 8, 10, 9, 11);

void setup() {

	Serial.begin(9600);  //In case you want to use the Serial Monitor later on...
	stepperMotor.setSpeed(300);  // Determines the speed at which the stepper motor will run... not sure of the units!
}

void loop() {

	/*
	To calibrate the stepper motor, we can refer to the information manual
	for the particular stepper motor being used. Depending on the number of gears
	and ratios, the number of steps per revolution (SPR) will change. Admittedly,
	I overheard that the particular steps for this motor (28BYJ-48) is 2048 steps,
	as the SPR is 32 and there is a 1/64 gear ratio. This means that to complete
	one full revolution, the motor must be stepped 2048 times (32 * 64).
	Alternatively, we can experimentally determine the SPR by attaching the motor
	to a protractor or large disc with degree markings, and commanding the motor to
	turn a certain number of steps, and measuring the angle turned.
	*/

	stepperMotor.setSpeed(500); // Speed it up cuz default is slow
	stepperMotor.step(750); //advances the stepper motor by a requested number of steps (750).
	delay(500);  // just a delay, for fun.
	stepperMotor.step(-750); //steps in the opposite direction
	delay(500);
	stepperMotor.step(2048); //steps to complete one full revolution
	delay(500); 
}
