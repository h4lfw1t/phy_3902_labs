//***********************************
// Arduino ON-OFF temperature control
// - Michel Godin
//***********************************

#include "CSVPrinter.h"

/**
 * @brief Holds the mean and standard deviation of thermistor readings.
 */
struct Stats {
    float mean;
    float stddev;
};

//*** Constants 
const float Tset = 65.0;    // set temperature in degrees celcius (ideally between 40 and 65)
const float Band = 1.0;     // Temperature band for hysteresis
const float Tmax = 75.0;    // Setting a maximum temperature. For safety, heater will be turned off when exceeding this temperature.
const int numSamples = 100; // number of samples to average for temperature measurement
const int gatePin = 9; // PWM pin to control MOSFET
const int thermistorPin = A0; // Analog pin connected to the thermistor
const long R_series = 100000; // series resistance for thermistor's voltage divider
const unsigned long RESPONSE_TIME_S = 60;
const unsigned long ActionTime = (unsigned long)(2 * RESPONSE_TIME_S * 1000); // ActionTime is twice the response time, in ms

//*** Variable definitions    
float temp_average; // average measured temperature
float Vo; // ADC voltage (digital) measured across thermistor
float Rt, lnRt; // thermistor resistance, natural log of thermistor resistance
float T_kelvin, T_celsius; // temperature (Kelvin), temperature (degrees Celsius)

//*** Variable declarations
Stats temp_stats; // struct to hold temperature statistics
float A = 0.7141095422e-3, B = 2.143243110e-4, C = 1.129790692e-7; // Steinhart-Hart coefficients

//*** Time associated variable definitions and declarations
unsigned long CurrentTime;            // ms
unsigned long PreviousTime = 0; // ms
unsigned long DeltaTime;                // ms
unsigned long MaxTime = 30;    // Time limit: Maximum duration of experiment in minutes until the heater is turned OFF.
unsigned long LastIntegralUpdate = 0; // Last time the integral was updated
unsigned long windowStartTime = 0;


//*** Some variables that are not used now, but might become useful when you implement PID control
float Error;        // The error (Tset - temp_average)
float Offset = 0.25; // offset for proportional control
float Previous_Error = 0.0; // necessary for the PID controller when calculating the integral and derivative
float Kp = 0.3; // proportional gain - you can tune this value
float Ki = 0.001; // integral gain, can be zero 
float Kd = 0.001; // derivative gain, can be zero
float Integral = 0.0; // Integral value: sum of the areas
float Derivative = 0.0; // Derivative value: slope
int Power;      // When implementing PID, Power will be calcuated and this value will be the PWM output between 0-255)
                // Power = (Kp*Error + Ki*Integral + Kd*Derivative) * 255;

// Derivative smoothing parameters
const int DERIV_WINDOW = 10; // Number of samples for rolling average
float errorBuffer[DERIV_WINDOW];
unsigned long timeBuffer[DERIV_WINDOW];
int bufferIndex = 0;
bool bufferFilled = false;

void setup() {
    pinMode(gatePin, OUTPUT);
    CSVPrinter::begin(9600);
    Serial.println("ON-OFF Control with PI-D");
    Serial.println("---DATA START---");
    CSVPrinter::printHeader("time(s),temp_mean(C),temp_stddev(C),output_power");
    // Initialize buffers
    for (int i = 0; i < DERIV_WINDOW; i++) {
        errorBuffer[i] = 0.0;
        timeBuffer[i] = 0;
    }
}

void loop() {
    get_time();
    temp_stats = measureTemperature(thermistorPin, numSamples);

    Error = (Tset - temp_stats.mean) / Band;

    // Reset Integral at the start of each ActionTime window
    if (CurrentTime - windowStartTime >= ActionTime) {
        Integral = 0.0;
        windowStartTime = CurrentTime;
    }

    // Accumulate error * dt within the window
    float dt = DeltaTime / 1000.0; // seconds
    Integral += Error * dt;

    // --- Derivative calculation with rolling average (of error) ---
    errorBuffer[bufferIndex] = Error;
    timeBuffer[bufferIndex] = CurrentTime;
    int oldestIndex = (bufferIndex + 1) % DERIV_WINDOW;
    bufferIndex = (bufferIndex + 1) % DERIV_WINDOW;
    if (bufferIndex == 0) bufferFilled = true;

    float Derivative = 0.0;
    if (bufferFilled) {
        float errorDiff = errorBuffer[bufferIndex] - errorBuffer[oldestIndex];
        float timeDiff = (timeBuffer[bufferIndex] - timeBuffer[oldestIndex]) / 1000.0; // seconds
        if (timeDiff > 0) {
            Derivative = -errorDiff / timeDiff;
        }
    }

    // --- PID calculation ---
    int out = (Offset + Error * Kp + Integral * Ki + Derivative * Kd) * 255;
    Power = constrain(out, 0, 255);

    analogWrite(gatePin, Power);

    CSVPrinter::printRow(CurrentTime/1000.0, temp_stats.mean, temp_stats.stddev, Power, 3);
    delay(10);
}


// Below, we define several functions that are used in the main LOOP()
// We use function to make the main LOOP() a little tidier

//* This function computes the average temperature for better results
Stats measureTemperature(int pin, int numSamples) {
    float temp_sum = 0.0;
    float temp_squared_sum = 0.0;
    float Vo, Rt, lnRt, T_kelvin, T_celsius;
    Stats stats;

    for (int m = 0; m < numSamples; m++) {
        Vo = analogRead(pin);
        Rt = R_series * (Vo / (1023.0 - Vo));
        lnRt = log(Rt);
        T_kelvin = (1.0 / (A + B * lnRt + C * pow(lnRt, 3)));
        T_celsius = T_kelvin - 273.15;
        temp_sum += T_celsius;
        temp_squared_sum += T_celsius * T_celsius;
        delay(10);
    }
    stats.mean = temp_sum / numSamples;
    float variance = (temp_squared_sum - numSamples * stats.mean * stats.mean) / (numSamples - 1);
    stats.stddev = sqrt(abs(variance));
    return stats;

// For safety: The following turns off the heater if the temperature exceed the pre-defined MAX temperature
    // if(temp_average >= Tmax){
    //     while(1){                 // Notice that this while condition is always true, so this will permanently stop the code until you reset the Arduino
    //         analogWrite(gatePin,0);     //turning off the heater
    //         Serial.println("Maximum temperature has been exceeded. Heater is turned OFF. Reset Arduino to restart the program");
    //         delay(5000);
    //     }
    // }    
}

//* This function keeps track of the time.
void get_time(){
    CurrentTime = millis();         // Time elapsed (in milliseconds) since the beginning
    DeltaTime = CurrentTime - PreviousTime;    // This "might" be useful when you implement integral or derivative control!
    PreviousTime = CurrentTime; // ready for next loop!

// For safety: The following IF statement prevents any experiment from lasting longer than "MaxTime" minutes
    if(CurrentTime >= MaxTime*60*1000){             // converting MaxTime from minutes to milliseconds
        while(1){
            analogWrite(gatePin,0);     //turning off the heater
            Serial.println("Maximum time has been reached, heater is turned OFF. Reset Arduino to restart the program");
            delay(5000);
        }
    }
}
