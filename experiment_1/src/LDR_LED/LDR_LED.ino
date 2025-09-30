// LDR_LED.ino
int fromLow = 100;
int fromHigh = 400;
// Note: toLow and toHigh are inverted to brighten LED when ldrValue increases
int toLow = 255;
int toHigh = 0;
int ldrValue; // LDR value as read by the analog input
int ledBrightness;  // mapped LED brightness (0-255)

void setup() {
	// Initialize serial communication
	Serial.begin(9600);
	Serial.println("LDR Value, LED Brightness");
}

void loop() {
	// Read the LDR value
	ldrValue = analogRead(A0);

	// Map the LDR value to LED brightness (0-255)
	// Increase the value of fromLow for a more pronounced result
	int ledBrightness = map(ldrValue, fromLow, fromHigh, toLow, toHigh);

	// Set the LED brightness
	analogWrite(9, ledBrightness);

	// Print the LDR value and LED brightness to the serial monitor
	Serial.print(ldrValue);
	Serial.print(", ");
	Serial.println(ledBrightness);

	delay(100);
}
