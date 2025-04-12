/** code for arduino device with MQ135 sensor

#include <MQ135.h>

#define SENSOR_PIN A0 /** Change A0 according to the port connected

MQ135 gasSensor(SENSOR_PIN);

void setup() {
    Serial.begin(9600);
}

void loop() {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');  // Read request
        command.trim();
        if (command == "GET") {  // If request is valid
            float ppm = gasSensor.getPPM();
            Serial.println(ppm);  // Send the sensor value
        }
    }
}
