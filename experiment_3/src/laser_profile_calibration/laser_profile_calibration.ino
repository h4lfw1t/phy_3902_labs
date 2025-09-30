# include <Servo.h>
# include <CSVPrinter.h>

// Define variables
int pos = 0;

// Define constants
const int SERVO_PIN = 9; // Pin connected to the servo signal wire
const int LASER_PIN = 3; // Pin connected to the laser
const int LDR_PIN = A0;  // Pin connected to the LDR
const int NUM_SAMPLES = 100; // Number of samples to average for LDR reading

Servo myServo;

void setup() {
    CSVPrinter::begin(9600);
    myServo.attach(SERVO_PIN);
    pinMode(LASER_PIN, OUTPUT);
    digitalWrite(LASER_PIN, HIGH); // Turn on laser
    
    // Print CSV header
    CSVPrinter::printHeader("position,ldr_reading");
}

void loop() {
    // Example: sweep servo from 0 to 180 degrees
    for (pos = 0; pos <= 180; pos += 5) {
        myServo.write(pos);
        delay(500); // Wait for servo to reach position
        
        // Take LDR reading
        int ldrValue = analogRead(LDR_PIN);
        
        // Print CSV row
        CSVPrinter::printRow(pos, ldrValue);
        
        delay(100);
    }
    
    // Optional: sweep back
    for (pos = 180; pos >= 0; pos -= 5) {
        myServo.write(pos);
        delay(500);
        
        int ldrValue = analogRead(LDR_PIN);
        CSVPrinter::printRow(pos, ldrValue);
        
        delay(100);
    }
}