#include "CSVPrinter.h"

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