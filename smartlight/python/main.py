import time
import os
import io
import base64
import json
import random

from arduino.app_utils import *
from paho.mqtt import client as mqtt_client
from arduino.app_bricks.audio_classification import AudioClassification
from arduino.app_bricks.web_ui import WebUI


# =========================================================
# GLOBAL CONFIG
# =========================================================

AUDIO_DIR = "/app/assets/audio"

broker = "broker.hivemq.com"
port = 1883

device_id = 1001
topic = f"id/{device_id}/sensores"

client_id = f"arduinoq-{random.randint(0, 1000)}"
client = None

last_publish_time = 0

# Sensor global state
temperature = 0.0
humidity = 0.0
luz = 0.0
decibelis = 0.0
intensity = 0.0
detection = False
motor = False


# =========================================================
# LOG
# =========================================================

def log(msg):
    print(f"[MQTT-LOG] {msg}")


print("Hello world!")


# =========================================================
# WEB UI
# =========================================================

def parse_data(data):
    if isinstance(data, str):
        return json.loads(data)
    return data if isinstance(data, dict) else {}


def on_run_classification(sid, data):
    try:
        parsed_data = parse_data(data)

        confidence = parsed_data.get("confidence", 0.5)
        audio_data = parsed_data.get("audio_data")
        selected_file = parsed_data.get("selected_file")

        input_audio = None

        if audio_data:
            audio_bytes = base64.b64decode(audio_data)
            input_audio = io.BytesIO(audio_bytes)

        elif selected_file:
            file_path = os.path.join(AUDIO_DIR, selected_file)

            if not os.path.exists(file_path):
                ui.send_message(
                    "classification_error",
                    {"message": f"Sample file not found: {selected_file}"},
                    sid
                )
                return

            with open(file_path, "rb") as f:
                input_audio = io.BytesIO(f.read())

        if input_audio:
            start_time = time.time() * 1000

            results = AudioClassification.classify_from_file(
                input_audio,
                confidence
            )

            diff = time.time() * 1000 - start_time

            response_data = {
                "results": results,
                "processing_time": diff
            }

            if results:
                response_data["classification"] = {
                    "class_name": results["class_name"],
                    "confidence": results["confidence"]
                }
            else:
                response_data["error"] = (
                    "No objects detected in the audio. "
                    "Try lowering the confidence threshold."
                )

            ui.send_message(
                "classification_complete",
                response_data,
                sid
            )

        else:
            ui.send_message(
                "classification_error",
                {"message": "No audio available for classification"},
                sid
            )

    except Exception as e:
        ui.send_message(
            "classification_error",
            {"message": str(e)},
            sid
        )


ui = WebUI()
ui.on_message("run_classification", on_run_classification)


# =========================================================
# MQTT
# =========================================================

def connect_mqtt():
    global client

    log("Creating MQTT client...")

    client = mqtt_client.Client(
        client_id=client_id,
        callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1
    )

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            log(f"Connected successfully ✔️ topic={topic}")
        else:
            log(f"Connection error ❌ code={rc}")

    def on_disconnect(client, userdata, rc):
        log(f"Disconnected from broker ⚠️ code={rc}")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    log(f"Connecting to broker {broker}:{port} ...")
    client.connect(broker, port)


# =========================================================
# MQTT PUBLISH
# =========================================================

def record_params():
    global client
    global last_publish_time
    global temperature, humidity, luz
    global decibelis, intensity

    try:
        current_time = time.time()

        # Publish every 30 seconds
        if current_time - last_publish_time < 30:
            return

        last_publish_time = current_time

        data = {
            "id": device_id,
            "temperatura": temperature,
            "humedad": humidity,
            "sonido": decibelis,
            "luz": intensity
        }

        payload = json.dumps(data)

        result = client.publish(topic, payload)

        if result[0] == 0:
            log(f"Published ✔️ topic={topic}")
            log(payload)
        else:
            log(f"Publish error ❌ status={result[0]}")

    except Exception as e:
        log(f"Exception publishing MQTT ❌ {str(e)}")


# =========================================================
# BRIDGE CALLBACK
# =========================================================

def get_sensor_data(
    temp: float,
    hum: float,
    l: float,
    db: float,
    inten: float,
    detec: bool,
    mot: bool
):
    global temperature
    global humidity
    global luz
    global decibelis
    global intensity
    global detection
    global motor

    print(
        f"raw values -> "
        f"temp={temp}, "
        f"hum={hum}, "
        f"luz={l}, "
        f"db={db}, "
        f"intensity={inten}, "
        f"detection={detec}, "
        f"motor={mot}"
    )

    temperature = temp
    humidity = hum
    luz = l
    decibelis = db
    intensity = inten
    detection = detec
    motor = mot

    record_params()


# =========================================================
# MAIN LOOP
# =========================================================

def loop():
    time.sleep(0.1)

    Bridge.call("control_function")
    Bridge.provide("get_sensor_data", get_sensor_data)


# =========================================================
# RUN
# =========================================================

connect_mqtt()
client.loop_start()

App.run(user_loop=loop)