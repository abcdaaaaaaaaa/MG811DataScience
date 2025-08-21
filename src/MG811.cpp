#include "MG811.h"
#include <math.h>

MG811::MG811(int bitadc, byte pin)
{
    _bitadc = pow(2, bitadc) - 1;
    _pin = pin;
}

struct GasData { float a, b, R2, minppm, maxppm, emf_min, emf_max; };

GasData gases[] = {
    {326.7924, -0.0017, 1.0,    100, 1000, 323.217, 324.2145}, // CH4
    {329.7936, -0.0039, 0.9049, 100, 1000, 320.6234, 323.616}, // C2H5OH
    {422.0278, -0.0481, 0.8772, 100, 10000, 264.1646, 323.616}, // CO
    {499.0689, -0.0722, 1.0,    400, 1000, 303.6658, 324.2145}  // CO2
};

void MG811::begin() {
    pinMode(_pin, INPUT);
}

float MG811::read() {
    int adc = analogRead(_pin);
    return (float)adc / (float)_bitadc;
}

float MG811::fmap(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

float MG811::inverseYaxb(float a, float y, float b) {
    return pow(y / a, 1.0 / b);
}

float MG811::correction_time(unsigned long t) {
    return (t < 20) ? t : fmod(t, 20.0);
}

float MG811::time_curve(float x) {
    if (x <= 1) return 325.79;
    else if (x <= 2) return fmap(x, 1, 2, 325.79, 326.15);
    else if (x <= 3) return fmap(x, 2, 3, 326.15, 325.05);
    else if (x <= 5) return fmap(x, 3, 5, 325.05, 288.06);
    else if (x <= 7) return 285.86 + (3.2 * pow(x - 4, -1.0587) - 1);
    else if (x <= 11) return 285.86;
    else if (x <= 13) return 285.86 + (3.2 * pow(14 - x, -1.0587) - 1);
    else if (x <= 15) return fmap(x, 13, 15, 288.06, 319.93);
    else if (x <= 17) return 324.87 - (5.94 * pow(x - 14, -1.6218) - 1);
    else if (x <= 19) return 324.87;
    else if (x <= 20) return fmap(x, 19, 20, 324.87, 325.79);
    else return NAN;
}

float MG811::calculateCorrection(unsigned long t) {
    float temp_corr_a = fmap(28, 20, 30, 523.094, 527.0596);
    float temp_corr_b = fmap(28, 20, 30, -0.0863, -0.0879);

    float a_corr = (temp_corr_a + 538.2376 + 499.0689) / 3.0;
    float b_corr = (temp_corr_b + -0.0733 + -0.0722) / 3.0;

    float x = correction_time(t);
    float curve = time_curve(x);
    return 3500.0 / inverseYaxb(a_corr, curve, b_corr);
}

float MG811::calculateppm(float SensorValue, float temp, float rh, float correction, String gas) {
    int idx = 0;
    if (gas == "CH4") idx = 0;
    else if (gas == "C2H5OH") idx = 1;
    else if (gas == "CO") idx = 2;
    else if (gas == "CO2") idx = 3;

    GasData g = gases[idx];
    float emf = fmap(SensorValue, 0, 1, g.emf_max, g.emf_min);
    
    float a_temp, b_temp;
    
    if (temp <= -10) {
        a_temp = 522.7202; b_temp = -0.0843;
    } else if (temp <= 0) {
        a_temp = fmap(temp, -10, 0, 522.7202, 517.0238);
        b_temp = fmap(temp, -10, 0, -0.0843, -0.0833);
    } else if (temp <= 10) {
        a_temp = fmap(temp, 0, 10, 517.0238, 520.9298);
        b_temp = fmap(temp, 0, 10, -0.0833, -0.0849);
    } else if (temp <= 20) {
        a_temp = fmap(temp, 10, 20, 520.9298, 523.094);
        b_temp = fmap(temp, 10, 20, -0.0849, -0.0863);
    } else if (temp <= 30) {
        a_temp = fmap(temp, 20, 30, 523.094, 527.0596);
        b_temp = fmap(temp, 20, 30, -0.0863, -0.0879);
    } else if (temp < 50) {
        a_temp = fmap(temp, 30, 50, 527.0596, 527.0802);
        b_temp = fmap(temp, 30, 50, -0.0879, -0.0891);
    } else if (temp >= 50) {
        a_temp = 527.0802; 
        b_temp = -0.0891;
    }
    
    float a_rh, b_rh;
    
    if (rh <= 40) {
        a_rh = 536.8846; b_rh = -0.0726;
    } else if (rh <= 65) {
        a_rh = fmap(rh, 40, 65, 536.8846, 538.2376);
        b_rh = fmap(rh, 40, 65, -0.0726, -0.0733);
    } else if (rh < 85) {
        a_rh = fmap(rh, 65, 85, 538.2376, 529.1227);
        b_rh = fmap(rh, 65, 85, -0.0733, -0.0717);
    } else if (rh >= 85) {
        a_rh = 529.1227; 
        b_rh = -0.0717;
    }

    float a_avg = (a_temp + a_rh + g.a * g.R2) / (2 + g.R2);
    float b_avg = (b_temp + b_rh + g.b * g.R2) / (2 + g.R2);

    return inverseYaxb(a_avg, emf, b_avg) * correction;
}


float MG811::TheoreticalCO2(float x) {
  float polynomial = 4.9961 * pow(x, 1) + 6.4881 * pow(x, 2) - 4.6000 * pow(x, 3);
  return 1000.0 - 600.0 * exp(-polynomial);
}
