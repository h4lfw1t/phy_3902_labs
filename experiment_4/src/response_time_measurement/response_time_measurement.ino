//***********************************
// Simple Arduino Step Response Measurement
//***********************************

const int gatePin = 9; // PWM pin to control MOSFET
const int thermistorPin = A0; // Analog pin connected to the thermistor
const long R_series = 100000; // series resistance for thermistor's voltage divider
float A = 0.7141095422e-3, B = 2.143243110e-4, C = 1.129790692e-7; // Steinhart-Hart coefficients

unsigned long stepTime = 0;
unsigned long responseTime = 0;
bool stepApplied = false;
float initialTemp = 0.0;
float targetTemp = 0.0;

float readTemperatureC(int pin) {
    float Vo = analogRead(pin);
    float Rt = R_series * (Vo / (1023.0 - Vo));
    float lnRt = log(Rt);
    float T_kelvin = (1.0 / (A + B * lnRt + C * pow(lnRt, 3)));
    return T_kelvin - 273.15;
}

void setup() {
    pinMode(gatePin, OUTPUT);
    Serial.begin(9600);
    delay(1000);
    Serial.println("Simple Step Response Measurement");
    // Measure initial temperature (average 10 samples)
    float sum = 0.0;
    for (int i = 0; i < 10; i++) {
        sum += readTemperatureC(thermistorPin);
        delay(100);
    }
    initialTemp = sum / 10.0;
    targetTemp = initialTemp + 5.0;
    Serial.print("Initial temperature: ");
    Serial.print(initialTemp, 2);
    Serial.println(" C");
    Serial.print("Target temperature (step): ");
    Serial.print(targetTemp, 2);
    Serial.println(" C");
    Serial.println("Applying step (heater ON)...");
    analogWrite(gatePin, 255); // Apply step
    stepTime = millis();
    stepApplied = true;
}

void loop() {
    if (!stepApplied) return;
    float temp = readTemperatureC(thermistorPin);
    unsigned long now = millis();
    float elapsed = (now - stepTime) / 1000.0;
    Serial.print("Time: ");
    Serial.print(elapsed, 1);
    Serial.print(" s, Temp: ");
    Serial.print(temp, 2);
    Serial.println(" C");

    float threshold = initialTemp + 0.63 * (targetTemp - initialTemp);
    if (temp >= threshold) {
        responseTime = now - stepTime;
        Serial.println();
        Serial.print("Response time (63% rise): ");
        Serial.print(responseTime / 1000.0, 2);
        Serial.println(" s");
        analogWrite(gatePin, 0); // Turn off heater
        Serial.println("Heater OFF. Done. Reset Arduino to repeat measurement.");
        stepApplied = false;
    }
    delay(1000);
}
