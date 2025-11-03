// LED_FADE.ino
int ledPin = 9;    // Defining a new variable called ledPin; LED will be connected to digital pin 9
									 // You don't need to define the channel as a variable, but it makes it easier if you want to
									 // change the pin number later on.
void setup() {
										// nothing happens in setup here
}

void loop() {
		// fade in from min to max in increments of 5.
		// We use a FOR loop to increment the fadeValue gradually, from 0 to 255
	for (int fadeValue = 0 ; fadeValue <= 255; fadeValue += 20) {
   
		// sets the value (range from 0 to 255):
		analogWrite(ledPin, fadeValue);
    
		// wait for 30 milliseconds to see the dimming effect. You can change the delay time if you want!
		delay(30);
	}

		// fade out from max to min in increments of 5 points:
		// We use a FOR loop to increment the fadeValue gradually, from 255 to 0

	for (int fadeValue = 255 ; fadeValue >= 0; fadeValue -= 20) {

		// sets the value (range from 0 to 255):
		analogWrite(ledPin, fadeValue);
    
		// wait for 30 milliseconds to see the dimming effect
		delay(30);
	}
}
