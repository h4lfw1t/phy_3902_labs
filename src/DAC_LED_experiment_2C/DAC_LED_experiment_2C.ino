#include <Wire.h>
#include <Adafruit_MCP4725.h>

// --- Structs ---

/**
 * @struct AnalogStats
 * @brief Holds the mean and standard deviation of analog readings.
 *
 * Used to store the average (mean) and standard deviation (stddev) of multiple analog readings.
 */
struct AnalogStats {
    float mean;   /**< The mean (average) value of the analog readings. */
    float stddev; /**< The standard deviation of the analog readings. */
};

/**
 * @brief Holds the result of a difference and its propagated error.
 */
struct DiffStats {
    float diff;
    float error;
};

// --- Constants ---
const float RESISTOR = 218.3; // Ohms
const float RESISTOR_TOLERANCE = 0.005; // 0.5%
const float DIODE_RESISTANCE = 0;  // Ohms
const uint8_t DAC_ADDR = 0x62;
const int DAC_STEPS = 51;
const float DAC_VOLTAGE_STEP = 0.1;
const int DAC_RESOLUTION = 4095;
const int ANALOG_READ_DELAY = 50;

// --- Globals ---
bool hasRun = false;
Adafruit_MCP4725 dac;

// --- Utility Functions ---

/**
 * @brief Calculates the difference and propagated error between two AnalogStats.
 * @param a First AnalogStats.
 * @param b Second AnalogStats.
 * @return DiffStats struct with difference and propagated error.
 */
DiffStats calcDiffStats(const AnalogStats& a, const AnalogStats& b) {
    DiffStats result;
    result.diff = a.mean - b.mean;
    result.error = propagate_addition_stddev(a.mean, b.mean, a.stddev, b.stddev);
    return result;
}

/**
 * @brief Maps a float value from one range to another.
 *
 * @param value The input value to map.
 * @param fromLow The lower bound of the input range.
 * @param fromHigh The upper bound of the input range.
 * @param toLow The lower bound of the output range.
 * @param toHigh The upper bound of the output range.
 * @return The mapped value in the output range.
 */
float float_map(float value, float fromLow, float fromHigh, float toLow, float toHigh) {
    return toLow + ((value - fromLow) * (toHigh - toLow)) / (fromHigh - fromLow);
}


/**
 * @brief Propagates standard deviation for addition or subtraction of two values.
 *
 * Uses error propagation formula for addition/subtraction.
 *
 * @param a First value.
 * @param b Second value.
 * @param stddev_a Standard deviation of the first value.
 * @param stddev_b Standard deviation of the second value.
 * @return The propagated standard deviation.
 */
float propagate_addition_stddev(float a, float b, float stddev_a, float stddev_b) {
    return sqrt(pow(a, 2) * pow(stddev_a, 2) + pow(b, 2) * pow(stddev_b, 2));
}


/**
 * @brief Prints a value in CSV format to the Serial output.
 *
 * @tparam T The type of the value to print.
 * @param value The value to print.
 * @param eol If true, prints a newline after the value; otherwise, prints a comma.
 */
template <typename T>
void printSerialCSV(T value, bool eol = false, int precision = 4) {
    if (eol) {
        Serial.println(value, precision);
    } else {
        Serial.print(value, precision);
        Serial.print(",");
    }
}

/**
 * @brief Prints a full CSV row of the experiment data to Serial.
 * @param outputVoltage The DAC output voltage.
 * @param a0 AnalogStats for A0.
 * @param a1 AnalogStats for A1.
 * @param a2 AnalogStats for A2.
 * @param a0_a1 DiffStats for A0-A1.
 * @param a1_a2 DiffStats for A1-A2.
 * @param current The calculated current (mA).
 * @param currentError The propagated error for current (mA).
 */
void printDataCSVRow(float outputVoltage, const AnalogStats& a0, const AnalogStats& a1, const AnalogStats& a2,
                     const DiffStats& a0_a1, const DiffStats& a1_a2, float current, float currentError) {
    Serial.print(String(outputVoltage) + ",");
    printSerialCSV(a0.mean);
    printSerialCSV(a0.stddev);
    printSerialCSV(a1.mean);
    printSerialCSV(a1.stddev);
    printSerialCSV(a2.mean);
    printSerialCSV(a2.stddev);
    printSerialCSV(a0_a1.diff);
    printSerialCSV(a0_a1.error);
    printSerialCSV(a1_a2.diff);
    printSerialCSV(a1_a2.error);
    printSerialCSV(current);
    printSerialCSV(currentError, true);
}

/**
 * @brief Reads the analog value from a pin and converts it to a voltage (0-5V).
 *
 * Takes multiple samples for stability and calculates mean and standard deviation.
 *
 * @param pin The analog pin to read from.
 * @param samples Number of samples to average (default: 10, max: 20).
 * @return AnalogStats struct containing mean and stddev of the voltage readings.
 */
AnalogStats readAnalogToVoltage(uint8_t pin, int samples = 10) {
    float values[20]; // Support up to 20 samples
    float total = 0;
    for (int i = 0; i < samples; i++) {
        values[i] = analogRead(pin);
        total += values[i];
        delay(5);
    }
    float mean = total / samples;
    float variance = 0;
    for (int i = 0; i < samples; i++) {
        variance += (values[i] - mean) * (values[i] - mean);
    }
    variance /= samples;
    float stddev = sqrt(variance);

    // Map to voltage
    AnalogStats stats;
    stats.mean = float_map(mean, 0, 1023, 0, 5.0);
    stats.stddev = float_map(stddev, 0, 1023, 0, 5.0);
    return stats;
}

// --- Analog Pin Helpers ---

/**
 * @brief Reads and returns voltage statistics from analog pin A0.
 * @return AnalogStats struct for A0.
 */
AnalogStats readA0() {
    return readAnalogToVoltage(A0);
}

/**
 * @brief Reads and returns voltage statistics from analog pin A1.
 * @return AnalogStats struct for A1.
 */
AnalogStats readA1() {
    return readAnalogToVoltage(A1);
}

/**
 * @brief Reads and returns voltage statistics from analog pin A2.
 * @return AnalogStats struct for A2.
 */
AnalogStats readA2() {
    return readAnalogToVoltage(A2);
}

// --- DAC Control ---

/**
 * @brief Sets the DAC output voltage by step index.
 *
 * Maps the step to the DAC's resolution and sets the output voltage.
 *
 * @param step The step index (0 to 51).
 */
void setDACVoltageByStep(int step) {
    int outputSignal = float_map(step, 0, 51, 0, 4095);
    dac.setVoltage(outputSignal, false);
}

// --- Data Acquisition ---

/**
 * @brief Acquires analog data for a given DAC step and prints results in CSV format.
 *
 * Sets the DAC output, reads analog pins, computes differences and currents, and prints all values.
 *
 * @param step The DAC step index.
 */
void acquireAndPrintData(int step) {
    float outputVoltage = step / 10.0;
    setDACVoltageByStep(step);
    delay(50);

    AnalogStats signalA0 = readA0();
    AnalogStats signalA1 = readA1();
    AnalogStats signalA2 = readA2();


    DiffStats a0_a1 = calcDiffStats(signalA0, signalA1);
    DiffStats a1_a2 = calcDiffStats(signalA1, signalA2);
    float current = (a0_a1.diff / RESISTOR) * 1000;
    // Error propagation for I = V/R: dI = I * sqrt( (dV/V)^2 + (dR/R)^2 )
    float dV = a0_a1.error;
    float dR = RESISTOR * RESISTOR_TOLERANCE;
    float currentError = current * sqrt( pow(dV / a0_a1.diff, 2 ) + pow(dR / RESISTOR, 2 ) );

    printDataCSVRow(outputVoltage, signalA0, signalA1, signalA2, a0_a1, a1_a2, current, currentError);

    delay(50);
}

// --- Header Printing ---

/**
 * @brief Prints the CSV header and experiment information to Serial.
 */
void printHeader() {
    for (int i = 0; i < 35; i++) Serial.print("-");
    Serial.println();
    Serial.println("DAC mounted to 0x62");
    Serial.println("Outputting voltage series.");
    Serial.println("out,A0,dA0,A1,dA1,A2,dA2,A0-A1,d(A0-A1),A1-A2,d(A1-A2),current (mA),d(current (mA))");
}

// --- Arduino Setup ---

/**
 * @brief Arduino setup function. Initializes Serial and DAC.
 */
void setup() {
    Serial.begin(9600);
    dac.begin(0x62);
    for (int i = 0; i < 35; i++) {
        Serial.print("-");
    }
    Serial.println();
    Serial.println("DAC mounted to 0x62");
}

// --- Arduino Loop ---

/**
 * @brief Arduino main loop. Runs the experiment once and prints results.
 */
void loop() {
    if (!hasRun) {
        printHeader();
        for (int i = 0; i < 51; i++) {
            acquireAndPrintData(i);
        }
        Serial.println("Finished");
        hasRun = true;
    }
}