#ifndef CSV_PRINTER_H
#define CSV_PRINTER_H

#include <Arduino.h>

/**
 * @brief A library for printing CSV formatted data to the Arduino Serial monitor.
 * 
 * This library provides convenient functions for outputting data in CSV format,
 * making it easy to collect and analyze experimental data from Arduino projects.
 * 
 * @author Generated for PHY3902 Labs
 * @version 1.0
 */

class CSVPrinter {
public:
    /**
     * @brief Initialize the CSV printer with Serial communication.
     * @param baudRate The baud rate for Serial communication (default: 9600)
     */
    static void begin(long baudRate = 9600);

    /**
     * @brief Prints a value in CSV format to the Serial output.
     * @tparam T The type of the value to print.
     * @param value The value to print.
     * @param eol If true, prints a newline after the value; otherwise, prints a comma.
     * @param precision Number of decimal places for floating point values (default: 4)
     */
    template <typename T>
    static void printValue(T value, bool eol = false, int precision = 4);

    /**
     * @brief Prints a CSV header row.
     * @param headers Array of header strings
     * @param numHeaders Number of headers in the array
     */
    static void printHeader(const char* headers[], int numHeaders);

    /**
     * @brief Prints a CSV header row using a single string with comma-separated values.
     * @param headerString String containing comma-separated header names
     */
    static void printHeader(const char* headerString);

    /**
     * @brief Starts a new CSV row (no output, just for organization)
     */
    static void startRow();

    /**
     * @brief Ends the current CSV row with a newline
     */
    static void endRow();

    /**
     * @brief Prints a complete CSV row with 2 values
     */
    template <typename T1, typename T2>
    static void printRow(T1 val1, T2 val2, int precision = 4);

    /**
     * @brief Prints a complete CSV row with 3 values
     */
    template <typename T1, typename T2, typename T3>
    static void printRow(T1 val1, T2 val2, T3 val3, int precision = 4);

    /**
     * @brief Prints a complete CSV row with 4 values
     */
    template <typename T1, typename T2, typename T3, typename T4>
    static void printRow(T1 val1, T2 val2, T3 val3, T4 val4, int precision = 4);
};

// Template function implementations


// Generic template for printValue (fallback for types not specialized below)
template <typename T>
void CSVPrinter::printValue(T value, bool eol, int /*precision*/) {
    if (eol) {
        Serial.println(value);
    } else {
        Serial.print(value);
        Serial.print(",");
    }
}

// Specialization for float
template <>
inline void CSVPrinter::printValue<float>(float value, bool eol, int precision) {
    if (eol) {
        Serial.println(value, precision);
    } else {
        Serial.print(value, precision);
        Serial.print(",");
    }
}

// Specialization for double
template <>
inline void CSVPrinter::printValue<double>(double value, bool eol, int precision) {
    if (eol) {
        Serial.println(value, precision);
    } else {
        Serial.print(value, precision);
        Serial.print(",");
    }
}

// Specialization for int
template <>
inline void CSVPrinter::printValue<int>(int value, bool eol, int /*precision*/) {
    if (eol) {
        Serial.println(value);
    } else {
        Serial.print(value);
        Serial.print(",");
    }
}

// Specialization for long
template <>
inline void CSVPrinter::printValue<long>(long value, bool eol, int /*precision*/) {
    if (eol) {
        Serial.println(value);
    } else {
        Serial.print(value);
        Serial.print(",");
    }
}

template <typename T1, typename T2>
void CSVPrinter::printRow(T1 val1, T2 val2, int precision) {
    printValue(val1, false, precision);
    printValue(val2, true, precision);
}

template <typename T1, typename T2, typename T3>
void CSVPrinter::printRow(T1 val1, T2 val2, T3 val3, int precision) {
    printValue(val1, false, precision);
    printValue(val2, false, precision);
    printValue(val3, true, precision);
}

template <typename T1, typename T2, typename T3, typename T4>
void CSVPrinter::printRow(T1 val1, T2 val2, T3 val3, T4 val4, int precision) {
    printValue(val1, false, precision);
    printValue(val2, false, precision);
    printValue(val3, false, precision);
    printValue(val4, true, precision);
}

// Non-template function implementations

void CSVPrinter::begin(long baudRate) {
    Serial.begin(baudRate);
}

void CSVPrinter::printHeader(const char* headers[], int numHeaders) {
    for (int i = 0; i < numHeaders; i++) {
        Serial.print(headers[i]);
        if (i < numHeaders - 1) {
            Serial.print(",");
        }
    }
    Serial.println();
}

void CSVPrinter::printHeader(const char* headerString) {
    Serial.println(headerString);
}

void CSVPrinter::startRow() {
    // This function is for organization/readability - no actual output
}

void CSVPrinter::endRow() {
    Serial.println();
}

#endif // CSV_PRINTER_H