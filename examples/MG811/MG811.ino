// (1) The library also supports data science applications such as gradient 4D Slope Estimation from Python!:
// (1) https://github.com/abcdaaaaaaaaa/MG811DataScience/tree/main/DataScience/4D_Slope

#include <MG811.h>

// For https://github.com/abcdaaaaaaaaa/MG811DataScience/blob/main/DataScience/4D_Slope/4D_Datas.xlsx the Time column should be defined as 9, 29, 49... 9 + 20k.
// If you want to define the Time function as 1, 2, 3 as in the standard, you can remove the delays or define it as delay(1000).
// On the other hand, the range in which the sensor can measure with the highest accuracy is specified in the data sheet as 7-11 seconds in 20-second periods.

#define ADC_BIT_RESU (12) // for ESP32
#define pin          (35) // D35 (ADC1)

unsigned long startTime = 0;
bool measuring = false;
bool firstReadDone = false;

float sensorVal, CO2, CH4, C2H5OH, CO, TheoreticalCO2, temp, rh, Correction;

MG811 sensor(ADC_BIT_RESU, pin);

void setup() {
    Serial.begin(115200); // for ESP32
    sensor.begin(); // WARNING: To get accurate results, please use the resistance (RL) value recommended in the data sheet.
}

void loop() {
    temp = 20.0; // DHT22 is recommended °C (Celsius)
    rh = 33.0;   // DHT22 is recommended %  (Relative Humidity)
    
    sensorVal = sensor.read();
  
    if (sensorVal > 0 && !measuring) {
      startTime = millis() / 1000;
      measuring = true;
      firstReadDone = false;
      delay(9000);

      Correction = sensor.calculateCorrection((millis() / 1000) - startTime);
      TheoreticalCO2 = sensor.TheoreticalCO2(sensorVal);
      
      CH4 = sensor.calculateppm(sensorVal, temp, rh, Correction, 0);
      C2H5OH = sensor.calculateppm(sensorVal, temp, rh, Correction, 1);
      CO = sensor.calculateppm(sensorVal, temp, rh, Correction, 2);
      CO2 = sensor.calculateppm(sensorVal, temp, rh, Correction, 3);
        
      Serial.println();
      Serial.print("Correction Coefficient: ");
      Serial.println(Correction);
      Serial.print("TheoreticalCO2: ");
      Serial.println(TheoreticalCO2);
      Serial.println();
      
      Serial.print("CO2: ");
      Serial.println(CO2);
      Serial.print("CH4: ");
      Serial.println(CH4);
      Serial.print("C2H5OH: ");
      Serial.println(C2H5OH);
      Serial.print("CO: ");
      Serial.println(CO);
      
      firstReadDone = true;

      Serial.println("----------");
      delay(20000);
    }
  
    while (measuring) {
      sensorVal = sensor.read();
      
      if (sensorVal == 0) {
        measuring = false;
        startTime = 0;
        break;
      }
      
      if (firstReadDone) { 
        Correction = sensor.calculateCorrection((millis() / 1000) - startTime);
        TheoreticalCO2 = sensor.TheoreticalCO2(sensorVal);

        CH4 = sensor.calculateppm(sensorVal, temp, rh, Correction, 0);
        C2H5OH = sensor.calculateppm(sensorVal, temp, rh, Correction, 1);
        CO = sensor.calculateppm(sensorVal, temp, rh, Correction, 2);
        CO2 = sensor.calculateppm(sensorVal, temp, rh, Correction, 3);
          
        Serial.print("Correction Coefficient: ");
        Serial.println(Correction);
        Serial.print("TheoreticalCO2: ");
        Serial.println(TheoreticalCO2);
        Serial.println();
        
        Serial.print("CO2: ");
        Serial.println(CO2);
        Serial.print("CH4: ");
        Serial.println(CH4);
        Serial.print("C2H5OH: ");
        Serial.println(C2H5OH);
        Serial.print("CO: ");
        Serial.println(CO);

        Serial.println("----------");
        delay(20000);
      }
    }
}
