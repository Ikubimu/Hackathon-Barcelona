# Smart Street Light

IoT intelligent street lighting system for cities, consisting of smart streetlights with environmental sensors and a real-time monitoring interface.

## Architecture

```
[Streetlight STM32] --- MQTT --- [Broker HiveMQ] --- [Web Interface]
        │                                           │
        └────────── Bridge API ─────────────────────┘
```

## Components

### 1. Smart Streetlight (`smartlight/`)

Platform: Arduino Zephyr (STM32)

**Sensors:**
- Temperature and Humidity (Modulino Thermo)
- Ambient Light (LDR)
- Noise Level (microphone)
- Presence Detection (PIR)

**Features:**
- Adaptive lighting based on ambient light and presence
- Automatic ventilation based on heat index
- MQTT communication every 30s
- Moving average filters for readings

### 2. Control Station (`external_ControlStation/`)

Technologies: Python Eel + SQLite + MQTT

> **Note**: Only works on Windows. Eel opens a native browser window (not accessible via localhost).

**Features:**
- Real-time visual dashboard
- Historical charts (Chart.js)
- Animated streetlight visualization
- SQLite storage
- Simulator for testing

## Usage

### Monitoring Interface

```bash
cd external_ControlStation
python main.py
```

Eel automatically opens a browser window.

### Streetlight

Compile and flash with PlatformIO:
```bash
cd smartlight
pio run -t upload
```

## MQTT

- Broker: `broker.hivemq.com:1883`
- Subscription topic: `id/+/sensores`
- Streetlight publish topic: `id/1001/sensores`

## Database

`historico_farolas.db` with table `lecturas`:
- farola_id, fecha, temperatura, humedad, sonido, luz