/*
    Image frame example for e-radionica.com Inkplate 6COLOR
    For this example you will need only USB cable and Inkplate 6COLOR.
    Select "Inkplate 6COLOR(ESP32)" from Tools -> Board menu.
    Don't have "Inkplate 6COLOR(ESP32)" option? Follow our tutorial and add it:
    https://e-radionica.com/en/blog/add-inkplate-6-to-arduino-ide/

    This example shows how you can set inkplate to show random pictures from web.

    Want to learn more about Inkplate? Visit www.inkplate.io
    Looking to get support? Write on our forums: http://forum.e-radionica.com/en/
    28 July 2020 by e-radionica.com
*/

#ifndef ARDUINO_INKPLATECOLOR
#error "Wrong board selection for this program, please select Inkplate 6COLOR in the boards menu."
#endif

#include <ArduinoJson.h>
#include "Inkplate.h"
#include "config.h"

#define REFRESH_INTERVAL_MINS 4

Inkplate display;

/* From https://github.com/SolderedElectronics/Inkplate-Arduino-library/issues/169#issuecomment-1331716568 */
double readBatteryVoltage()
{
    uint16_t rawADC;
    double voltage;
  
    // Set PCAL P1-1 to output. Do a ready-modify-write operation.
    pcal6416ModifyReg(0x07, 1, 0);

    // Set pin P1-1 to the high -> enable MOSFET for battery voltage measurement.
    pcal6416ModifyReg(0x03, 1, 1);

    // Wait a little bit
    delay(5);

    // Read analog voltage. Battery measurement is connected to the GPIO35 on the ESP32.
    rawADC = analogRead(35);

    // Turn off the MOSFET.
    pcal6416ModifyReg(0x03, 1, 0);

    // Calculate the voltage
    voltage = rawADC / 4095.0 * 3.3 * 2;

    // Return voltage.
    return voltage;
}

void pcal6416ModifyReg(uint8_t _reg, uint8_t _bit, uint8_t _state)
{
    uint8_t reg;
    uint8_t mask;
    const uint8_t pcalAddress = 0b00100000;
  
    Wire.beginTransmission(pcalAddress);
    Wire.write(_reg);
    Wire.endTransmission();

    Wire.requestFrom(pcalAddress, (uint8_t) 1);
    reg = Wire.read();

    mask = 1 << _bit;
    reg = ((reg & ~mask) | (_state << _bit));
  
    Wire.beginTransmission(pcalAddress);
    Wire.write(_reg);
    Wire.write(reg);
    Wire.endTransmission();
}

int fetchUntilDaytimeValue(const char* url, const char* timezone)
{
    char buffer[256];
    StaticJsonDocument<JSON_OBJECT_SIZE(2)> doc;
    int32_t resp_len = 1024;

    if (sizeof(url) + sizeof(timezone) >= 256) { // 256 is valid because we chop off one \0 there
        return -1;
    }

    if (sizeof(url) < 1) {
        return -2;
    }

    strncpy(buffer, url, sizeof(buffer));
    if (url[sizeof(url) - 1] != '/') {
        strncat(buffer, "/", sizeof(buffer) - 1);
    }
    strncat(buffer, timezone, sizeof(buffer) - 1);

    uint8_t* resp = display.downloadFile(buffer, &resp_len);
    if (resp == NULL) {
        return -3;
    }

    DeserializationError error = deserializeJson(doc, (char*) resp, resp_len);
    free(resp);
    if (error) {
        return -4;
    }

    if (strncmp(doc["status"] | "error", "error", 5) == 0) {
        return -5;
    }

    return doc["seconds"];
}

void setup()
{
    int ret = 0;
    int sleep_time;
    Serial.begin(115200);
    display.begin();

    // Join wifi
    display.joinAP(WIFI_SSID, WIFI_PASSWORD);
    Serial.println("joined wifi");

    ret = display.drawImage(EINK_URL, display.PNG, 0, 0, true, false);
    Serial.println(ret);

    display.setCursor(500, 20);
    display.setTextColor(INKPLATE_BLUE);
    display.setTextSize(2);
    display.print(readBatteryVoltage(), 2);
    display.print("V");

    display.display();

    sleep_time = fetchUntilDaytimeValue(API_URL, TIMEZONE);
    if (sleep_time <= 0) {
        if (sleep_time < 0) {
            Serial.print(F("Something went fucky: "));
            Serial.println(sleep_time);
        }
        sleep_time = REFRESH_INTERVAL_MINS * 60;
    }

    // Enable wakeup from deep sleep on gpio 36 (wake button)
    esp_sleep_enable_ext0_wakeup(GPIO_NUM_36, LOW);

    Serial.print("Going to sleep for ");
    Serial.print(sleep_time);
    Serial.println(" seconds");
    display.setPanelDeepSleep(false);
    esp_sleep_enable_timer_wakeup(sleep_time * 1000ll * 1000ll);
    esp_deep_sleep_start();
}

void loop()
{
    // Never here, as deepsleep restarts esp32
}
