#ifndef MG811_H
#define MG811_H
#include <Arduino.h>

class MG811 {
public:
    MG811(int bitadc, byte pin);
    void begin();
    float read();
    float calculateCorrection(float x);
    float calculateppm(float SensorValue, float temp, float rh, float correction, int idx);
    float TheoreticalCO2(float x);
    float correction_time(float t);
    
private:
    byte _pin;
    int _bitadc;
    float fmap(float x, float in_min, float in_max, float out_min, float out_max);
    float inverseYaxb(float a, float y, float b);
    float time_curve(float x);
};
                    
#endif
