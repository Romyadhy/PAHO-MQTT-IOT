import time
import requests
import paho.mqtt.client as mqtt

# ====== Konfigurasi Manual ======
MQTT_BROKER = "192.168.88.88"    # IP broker di RPi Anda
MQTT_PORT   = 1883
MQTT_TOPIC  = "smartgreengarden/sensor/temperature"

# URL Firebase (Realtime Database) – ganti sesuai project
FB_URL = "https://hydrohealth-project-9cf6c-default-rtdb.asia-southeast1.firebasedatabase.app/esp32info"

POLL_SECONDS = 20  # interval polling Firebase
# =================================

# Setup MQTT client
client = mqtt.Client("fb-bridge")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

def get_latest_temp():
    try:
        r = requests.get(FB_URL, timeout=10)
        data = r.json()
        if not data: 
            return None

        # Ambil tanggal terbaru
        latest_day = max(data.keys())
        # Ambil jam terbaru di dalam tanggal tsb
        latest_time = max(data[latest_day].keys())
        node = data[latest_day][latest_time]

        # Ambil field sensor_suhu_air
        if "sensor_suhu_air" in node:
            return float(node["sensor_suhu_air"])
        else:
            return None
    except Exception as e:
        print("Error ambil Firebase:", e)
        return None

last_temp = None

while True:
    temp = get_latest_temp()
    if temp is not None:
        if last_temp is None or abs(temp - last_temp) > 0.05:
            client.publish(MQTT_TOPIC, f"{temp:.2f}")
            print(f"Publish suhu: {temp:.2f} °C")
            last_temp = temp
    else:
        print("⚠️ Tidak ada data suhu ditemukan.")

    time.sleep(POLL_SECONDS)
