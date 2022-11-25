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

#include "Inkplate.h"
#include "config.h"

#define REFRESH_INTERVAL_MINS 4

Inkplate display;

void setup()
{
    int ret = 0;
    //Serial.begin(115200);
    display.begin();

    // Join wifi
    display.joinAP(WIFI_SSID, WIFI_PASSWORD);
    //Serial.println("joined wifi");

    ret = display.drawImage(EINK_URL, display.PNG, 0, 0, true, false);
    //Serial.println(ret);

    display.setCursor(500, 20);
    display.setTextColor(INKPLATE_BLUE);
    display.setTextSize(2);
    display.print(display.readBattery(), 2);
    display.print("V");

    display.display();

    // Enable wakeup from deep sleep on gpio 36 (wake button)
    esp_sleep_enable_ext0_wakeup(GPIO_NUM_36, LOW);

    //Serial.println("Going to sleep");
    display.setMCPForLowPower();
    display.setPanelDeepSleep(false);
    esp_sleep_enable_timer_wakeup(REFRESH_INTERVAL_MINS * 60ll * 1000ll * 1000ll);
    esp_deep_sleep_start();
}

void loop()
{
    // Never here, as deepsleep restarts esp32
}
