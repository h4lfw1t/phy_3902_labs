//***********************************
// Arduino ON-OFF temperature control
// - Michel Godin
//***********************************

//*** Constants 
const float Tset = 65.0;    // set temperature in degrees celcius (ideally between 40 and 65)
const float Band = 3.0;     // Temperature band for hysteresis: not used yet!
const float Tmax = 75.0;    // Setting a maximum temperature. For safety, heater will be turned off when exceeding this temperature.
const int numSamples = 100; // number of samples to average for temperature measurement
const int gatePin = 9; // PWM pin to control MOSFET
const long R_series = 100000; // series resistance for thermistor's voltage divider

//*** Variable definitions    
float temp_average; // average measured temperature
float temp_relative; // relative temperature with respect to Tset
float Vo; // ADC voltage (digital) measured across thermistor
float Rt, lnRt; // thermistor resistance, natural log of thermistor resistance
float T_kelvin, T_celsius; // temperature (Kelvin), temperature (degrees Celsius)

//*** Variable declarations
float temp_sum = 0.0; // sum of measured temperatures
float temp_squared_sum = 0.0; // sum of squared measured temperatures
float A = 0.7141095422e-3, B = 2.143243110e-4, C = 1.129790692e-7; // Steinhart-Hart coefficients

//*** Time associated variable definitions and declarations
unsigned long CurrentTime;            // ms
unsigned long PreviousTime = 0; // ms
unsigned long DeltaTime;                // ms
unsigned long MaxTime = 30;    // Time limit: Maximum duration of experiment in minutes until the heater is turned OFF.

//*** Some variables that are not used now, but might become useful when you implement PID control
float Error;        // The error (Tset - temp_average)
float Previous_Error = 0.0; // necessary for the PID controller when calculating the integral and derivative
float Kp = 0.3; // proportional gain - you can    
float Ki = 0.00001; // integral gain, can be zero 
float Kd = 0.0; // derivative gain, can be zero
float Integral = 0.0; // Integral value: sum of the areas
float Derivative = 0.0; // Derivative value: slope
int Power;        // When implementing PID, Power will be calcuated and this value will be the PWM output between 0-255)
                            // Power = (Kp*Error + Ki*Integral + Kd*Derivative) * 255;

/**
 * @brief Holds the mean and standard deviation of thermistor readings.
 */
struct TempStats {
    float mean;
    float stddev;
};

void setup() {
    
    pinMode(gatePin, OUTPUT);     
    Serial.begin(9600);
    Serial.println("ON-OFF Control");
    Serial.println("Elapsed_time_(sec),Measured_temperature_(C),Relative_temperature_(C),Output_power");    
}

void loop() {
    // This main loop is implementing ON-OFF temperature control.
    get_time();                         // This custom function is defined below. It determines the current time elapsed since the beginning. Current time is store in the variable "CurrentTime"
    measureTemperature();     // This custom function is defined below. It measures the temperature and stores the average in the variable "temp_average"

//*** This IF statement is the actual ON-OFF control
    if(temp_relative <= - Band / 2.0) {
            Power = 255;
            analogWrite(gatePin, Power);        // If measured temperature is LOWER than setpoint, the heater is turned ON
    }
    else if(temp_relative >= Band / 2.0) {
        Power = 0;
        analogWrite(gatePin, Power);        // If measured temperature is HIGHER than setpoint, the heater is turned OFF
    }

    Serial.println(String(CurrentTime/1000.0) + "," + String(temp_average) + "," + String(temp_relative) + "," + String(Power));    //sending time and temperature to the serial monitor
    delay(50);
    
}


// Below, we define several functions that are used in the main LOOP()
// We use function to make the main LOOP() a little tidier

//* This function computes the average temperature for better results
void measureTemperature(){
    for(int m=1;m<=numSamples;m++){
        Vo = analogRead(A0); // read analog to digital converter value
        Rt = R_series * (Vo / (1023 - Vo)); 
        lnRt = log(Rt);
        T_kelvin = (1.0 / (A + B*lnRt + C*pow(lnRt, 3)));
        T_celsius = T_kelvin - 273.15; 
        temp_sum += T_celsius;
        delay(10); // small delay to allow ADC to stabilize
    }
    temp_average = temp_sum/numSamples;
    temp_relative = temp_average - Tset;
    temp_sum = 0.0;


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
