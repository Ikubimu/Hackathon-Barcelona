import eel
import json
import sqlite3
import paho.mqtt.client as mqtt
from datetime import datetime
import threading
import time
import random

eel.init('web2.0')
DB_NAME = 'historico_farolas.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lecturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farola_id TEXT,
            fecha TEXT,
            temperatura REAL,
            humedad REAL,
            sonido REAL,
            luz REAL
        )
    ''')
    conn.commit()
    conn.close()

def guardar_en_db(farola_id, datos):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO lecturas (farola_id, fecha, temperatura, humedad, sonido, luz)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(farola_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              round(datos.get('temperatura', 0), 2), 
              round(datos.get('humedad', 0), 2),
              round(datos.get('sonido', 0), 2), 
              round(datos.get('luz', 0), 2)))
        conn.commit()
        conn.close()
    except: pass

estado_memoria = {}

@eel.expose
def obtener_historico(f_id, limite=20):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT fecha, temperatura, humedad, sonido, luz FROM lecturas WHERE farola_id = ? ORDER BY id DESC LIMIT ?', (str(f_id), limite))
        filas = cursor.fetchall()
        conn.close()
        return [{"fecha": f[0], "temperatura": f[1], "humedad": f[2], "sonido": f[3], "luz": f[4]} for f in filas][::-1]
    except: return []

@eel.expose
def inicializar_web(f_id):
    return {"historico": obtener_historico(f_id), "actual": estado_memoria.get(str(f_id))}

def simulador_sensores():
    ids = ["1001", "2000", "3000"]
    while True:
        for f_id in ids:
            datos = {
                "temperatura": round(random.uniform(20, 38), 2),
                "humedad": round(random.uniform(30, 90), 2),
                "sonido": round(random.uniform(40, 95), 2),
                "luz": round(random.uniform(100, 1000), 2)
            }
            estado_memoria[f_id] = datos
            guardar_en_db(f_id, datos)
            try: eel.notificar_datos(f_id, datos)()
            except: pass
        time.sleep(4)

def on_connect(client, userdata, flags, rc):
    if rc == 0: client.subscribe("id/+/sensores")

def on_message(client, userdata, msg):
    try:
        f_id = msg.topic.split('/')[1]
        payload = json.loads(msg.payload.decode())
        # Redondear datos entrantes por si el broker manda muchos decimales
        datos = {k: round(v, 2) for k, v in payload.items() if isinstance(v, (int, float))}
        estado_memoria[f_id] = datos
        guardar_en_db(f_id, datos)
        try: eel.notificar_datos(f_id, datos)()
        except: pass
    except: pass

if __name__ == "__main__":
    init_db()
    threading.Thread(target=simulador_sensores, daemon=True).start()
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect("broker.hivemq.com", 1883, 60)
        client.loop_start()
    except: pass
    eel.start('index.html', size=(1200, 950))