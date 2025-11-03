// THERMISTOR.ino
//*******************************************************************
// by M. Godin 2021
//*******************************************************************

//Before starting, we will define several variables:

float Vo;           // measured voltage across thermistor
float R0 = 100000;  // other resistor value in ohms 
float Vin = 1023.0; // supply voltage (1023 represents the digital value corresponding to 5V)
float lnRt;         // natural log of thermistor value
float Rt;           // calculated thermistor resistance value
float Tk, Tc;       // temperature (Kelvin), temperature (degrees Celsius) - note that you declare two variables on a single line!
float A = 0.7141095422e-3, B = 2.143243110e-4, C = 1.129790692e-7; // Steinhart-Hart coefficients

void setup() {
	Serial.begin(9600);       // We will be writing some information to the Serial Monitor. This initiates the communication protocol.
	Serial.println("T(Kelvin),  T(°C),   R(thermistor)" );  // Writing a header line to identify the columns. The "println" write the text and skips to the next line.
}

void loop() {

	Vo = analogRead(A0); // read analog to digital converter value. Read the voltage on pin A0.
	Rt = R0 * (Vo / (Vin - Vo));  // Calculates Rt from the measured Vo.
	lnRt = log(Rt);

	// Best way to calibrate would be to measure at a known temperature and compare the actual value to the computed value (e.g. 273.15 K)

	Tk = (1.0 / (A + B * lnRt + C * pow(lnRt, 3))); // you will need to change this to the correct formula to get the temperature in Kelvin!
	Tc = Tk - 273.15; // you will need to change this to the correct formula to get the temperature in Celcius!
  

	// The following will write some values to the Serial Monitor window. Open the Serial Monitor from the meny TOOLS>Serial Monitor
	Serial.print(Tk);
	Serial.print(" K  ;  ");
	Serial.print(Tc);
	Serial.print(" C  ;  ");
	Serial.print(Rt);
	Serial.println(" Ohms");
    
		delay(1000);
}
