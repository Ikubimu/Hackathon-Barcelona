#include <Arduino_Modulino.h>
#include "Arduino_RouterBridge.h"
#include "Adafruit_VEML7700.h"

// Configuración de Pines
#define LED_BUILTIN 42
#define LDR_PINOUT 16
#define MICROPHONE_PINOUT 17
#define LED_PWM_PINOUT 8
#define PIR_PINOUT 9
#define MOTOR 7

// Configuración de Filtros
#define WINDOW_SIZE 5

struct MovingAverage {
  float readings[WINDOW_SIZE];
  int index = 0;
  float sum = 0;
  
  float update(float newValue) {
    sum -= readings[index];
    readings[index] = newValue;
    sum += readings[index];
    index = (index + 1) % WINDOW_SIZE;
    return sum / WINDOW_SIZE;
  }
};

// Instancias de filtros
MovingAverage avgTemp, avgHum, avgLuz,avgDb;
ModulinoThermo thermo;

struct Data {
  float temperature;
  float humidity;
  float luz;
  float db;
  float heatIndex;
  float intensity;
  bool motor;
  bool detection;
};

void setup() {
  Modulino.begin();
  thermo.begin();
  Monitor.begin();
  Bridge.begin();
  
  Bridge.provide("control_function", control_function);
  Bridge.provide("set_motor_state", set_motor_state);
  
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PIR_PINOUT, INPUT);
  pinMode(MOTOR, OUTPUT);
  pinMode(LED_PWM_PINOUT, OUTPUT);
}

void loop() {
  // El loop se mantiene vacío para el Bridge
}

void control_function() {
  digitalWrite(LED_BUILTIN, HIGH);
  
  Data data;
  
  // 1. Lectura y Filtrado de variables
  data.temperature = avgTemp.update(thermo.getTemperature());
  data.humidity = avgHum.update(thermo.getHumidity());
data.luz = avgLuz.update(analogRead(LDR_PINOUT));
  data.db = leerDecibelios();
  // 2. Cálculo del Índice de Calor (Simplificado)
  // Evalúa la sensación térmica para activar el ventilador
  data.heatIndex = calculateHeatIndex(data.temperature, data.humidity);
  
  // 3. Lógica del Motor (Ventilador) automática
  // Si el índice de calor supera los 28°C, encendemos el ventilador
  data.motor = (data.heatIndex > 28.0);
  digitalWrite(MOTOR, data.motor ? HIGH : LOW);
   data.detection = digitalRead(PIR_PINOUT);
  // 4. Lógica de Iluminación y Presencia
  data.intensity = set_brightness_intensity(data.luz,data.detection);
 
   
  // 5. Notificación al Bridge
  Bridge.notify("get_sensor_data", 
                 data.temperature, 
                 data.humidity, 
                 data.luz, 
                 data.db,
                 data.intensity, 
                 data.detection, 
                 data.motor);
                 
  digitalWrite(LED_BUILTIN, LOW);
}

// Función para calcular la sensación térmica
float calculateHeatIndex(float t, float h) {
  return t + 0.55 * (h / 100.0) * (t - 14.5);
}

float offset = 512.0; 

float leerDecibelios() {
  long sumaCuadrados = 0;
  int muestras = 100; // Tomamos 100 muestras rápidas para captar la onda
  
  for (int i = 0; i < muestras; i++) {
    int lectura = analogRead(MICROPHONE_PINOUT);
    float amplitud = lectura - offset; // Centramos la señal en 0
    sumaCuadrados += (amplitud * amplitud);
  }
  
  // Calculamos el valor RMS (Root Mean Square)
  float rms = sqrt(sumaCuadrados / muestras);
  
  // Convertimos a escala logarítmica
  // El valor '1.0' es la referencia de silencio. 
  // El '+ 40' es el ajuste (calibration) para que un susurro empiece en 40dB.
  float db = 20.0 * log10(rms + 1.0) + 40.0;
  
  // Limitar para que no dé valores extraños en silencio absoluto
  if (db < 30) db = 30; 
  
  return db;
}
int set_brightness_intensity(float value,bool detection) {
  int intensity;
  if(detection == false){
    analogWrite(LED_PWM_PINOUT, 0);
    return 0;
  }
  if (value <= 400) {
    intensity = 255;
  } else if (value >= 550) {
    intensity = 0;
  } else {
    intensity = (550 - (int)value) * 255 / 150;
  }
  analogWrite(LED_PWM_PINOUT, intensity);
  return intensity;
}

void set_motor_state(bool state) {
  digitalWrite(MOTOR, state ? HIGH : LOW);
}