// Arduino code to experimentally determine the specific heat capacity of a metal block
// Block mass, heater resistance, and series resistor are defined as constants
// Heater is controlled via PWM on pin 9, thermistor is read from A0
// Data is output as CSV: time(s), temp(C), voltage(V), current(A), power(W)

#include "CSVPrinter.h"

const float m_block = 24.63; // mass of the aluminum block in grams
const float dm_block = 0.005; // uncertainty in mass of the aluminum block in grams
const float R_heater = 15.7; // resistance of the heater in ohms
const float dR_heater = 0.1; // uncertainty in heater resistance
const float R_series = 100000.0; // series resistor for thermistor voltage divider
const int heaterPin = 9; // PWM pin for heater
const int thermistorPin = A0; // Analog pin for thermistor
const float V_supply = 5.0; // Supply voltage (V)
const int numSamples = 100; // Number of samples for temperature averaging
const int pwmValue = 200; // PWM value (0-255) for heater (adjust as needed)

// Steinhart-Hart coefficients for thermistor (update for your thermistor)
const float A = 0.7141095422e-3, B = 2.143243110e-4, C = 1.129790692e-7;

struct Stats {
    float mean;
    float stddev;
};

unsigned long startTime;

// Cycle control variables
const unsigned long interval_ms = 2UL * 60UL * 1000UL; // 2 minutes in ms
int phase = 0; // 0: heating, 1: cooling
int cycle_count = 0;
const int max_cycles = 2; // 2 heating + 2 cooling phases
unsigned long phase_start_time = 0;
bool finished = false;

void setup() {
    pinMode(heaterPin, OUTPUT);
    CSVPrinter::begin(9600);
    Serial.println("Specific Heat Capacity Experiment");
    Serial.println("---DATA START---");
    CSVPrinter::printHeader("time(s),temp_mean(C),temp_stddev(C),voltage(V),current(A),power(W)");
    startTime = millis();
    phase_start_time = millis();
}

void loop() {
    if (finished) {
        analogWrite(heaterPin, 0); // Ensure heater is off
        delay(1000);
        return;
    }

    unsigned long now = millis();
    // Determine if we need to switch phase
    if ((now - phase_start_time) >= interval_ms) {
        phase_start_time = now;
        phase = 1 - phase; // Toggle phase: 0 <-> 1
        cycle_count++;
        if (cycle_count >= 2 * max_cycles) {
            finished = true;
            analogWrite(heaterPin, 0); // Turn off heater
        }
    }

    //TODO: Implement a static phase to gauge the heat loss to the environment
    //      This will measure the power required to maintain temperature, which
    //      can be added to the calculations for more accurate specific heat capacity.

    // Set heater state
    if (!finished && phase == 0) {
        analogWrite(heaterPin, pwmValue); // Heating
    } else {
        analogWrite(heaterPin, 0); // Cooling
    }

    // Measure temperature
    Stats temp_stats = measureTemperature(thermistorPin, numSamples);

    // Calculate heater voltage and current
    float V_heater = (phase == 0 && !finished) ? (V_supply * pwmValue / 255.0) : 0.0;
    float I_heater = (phase == 0 && !finished) ? (V_heater / R_heater) : 0.0;
    float P_heater = (phase == 0 && !finished) ? (V_heater * I_heater) : 0.0;

    // Log data
    float t = (now - startTime) / 1000.0;
    CSVPrinter::printRow(t, temp_stats.mean, temp_stats.stddev, V_heater, I_heater, P_heater, 3);

    delay(1000); // Log every second
}

Stats measureTemperature(int pin, int n) {
    float temp_sum = 0.0, temp_sq_sum = 0.0;
    for (int i = 0; i < n; i++) {
        float Vo = analogRead(pin);
        float Rt = R_series * (Vo / (1023.0 - Vo));
        float lnRt = log(Rt);
        float T_kelvin = 1.0 / (A + B * lnRt + C * pow(lnRt, 3));
        float T_celsius = T_kelvin - 273.15;
        temp_sum += T_celsius;
        temp_sq_sum += T_celsius * T_celsius;
        delay(5);
    }
    Stats stats;
    stats.mean = temp_sum / n;
    float variance = (temp_sq_sum - n * stats.mean * stats.mean) / (n - 1);
    stats.stddev = sqrt(abs(variance));
    return stats;
}