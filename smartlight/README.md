# Smart Street Light

Intelligent street lighting system with environmental sensors and presence detection.

## Hardware

| Component | Pins | Description |
|-----------|------|-------------|
| LED Builtin | 42 | Activity indicator |
| LDR | 16 | Ambient light sensor |
| Microphone | 17 | Decibel sensor |
| LED PWM | 8 | LED lighting output |
| PIR | 9 | PIR presence sensor |
| Motor | 7 | Fan/Motor |

Platform: Arduino Zephyr (STM32)

## Features

### Sensors and Readings
- **Temperature and Humidity**: Measured via Modulino Thermo with moving average filter (window=5)
- **Ambient Light**: Filtered analog LDR reading
- **Noise Level**: RMS of 100 samples → logarithmic dB conversion

### Control Logic

**Adaptive Lighting** (`set_brightness_intensity`):
- No PIR detection → LED off
- LDR < 400 → Maximum intensity (255)
- LDR > 550 → Minimum intensity (0)
- Range 400-550 → Linear interpolation

**Automatic Ventilation**:
- Calculates heat index: `heatIndex = t + 0.55 * (h/100) * (t - 14.5)`
- Activates motor if heatIndex > 28°C

### Communication

Bridge API with notifications:
```
Bridge.notify("get_sensor_data", temp, hum, luz, db, intensity, detection, motor)
```

## MQTT

Broker: `broker.hivemq.com:1883`
Topic: `id/{device_id}/sensores`

JSON payload format:
```json
{
  "id": 1001,
  "temperatura": 25.5,
  "humedad": 60.2,
  "sonido": 45.3,
  "luz": 180
}
```

Published every 30 seconds.

## Noise Analysis

Web server at `http://localhost:7000` for audio classification.

Allows analyzing different types of ambient noises using AudioClassification.

## Control Interface

Located in `external_ControlStation/`

- Eel frontend (web2.0)
- SQLite database (historico_farolas.db)
- Subscribed to topics `id/+/sensores`
- Sensor simulator for testing

### Usage

```bash
cd external_ControlStation
python main.py
```

Access at `http://localhost:8000`

## Streetlight Visualization

The web interface includes an animated visualization of the streetlight:
- **Foco**: Changes intensity based on light reading
- **Vapor**: Animated condensation effect
- **Alerta**: Status/detection indicator