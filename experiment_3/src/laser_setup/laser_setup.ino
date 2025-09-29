
int const LASER_PIN = 3;
int const LDR_FEED_PIN = A0;
bool hasRun = false;

float averageReadLDR(int pin, int numSamples) {
    long total = 0;
    for (int i = 0; i < numSamples; i++) {
        total += analogRead(pin);
        delay(10); // Small delay to allow ADC to stabilize
    }
    return total / (float)numSamples;
}

void setup() {
    pinMode(LASER_PIN, OUTPUT);
    pinMode(LDR_FEED_PIN, INPUT);
    Serial.begin(115200);
}

void loop() {
    if (!hasRun) {
        digitalWrite(LASER_PIN, HIGH); // Turn the laser on

        float ldrValue = averageReadLDR(LDR_FEED_PIN, 100);
        Serial.print("Average LDR Value: ");
        Serial.println(ldrValue);

        digitalWrite(LASER_PIN, LOW);  // Turn the laser off
        Serial.println("Laser deactivated.");
        hasRun = true;                 // Ensure this block runs only once
    }
}