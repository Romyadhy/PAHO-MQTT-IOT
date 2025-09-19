import paho.mqtt.client as mqtt
import requests
import time
import threading
import json
from concurrent.futures import ThreadPoolExecutor

# === Konfigurasi Telegram ===
TELEGRAM_BOT_TOKEN = '7744245206:AAHGAlfLOK3F3ECSpVHSEQJIfxDay4qT5fo'
TELEGRAM_CHAT_ID = '5344109406'
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# === Konfigurasi MQTT ===
MQTT_BROKER = "192.168.88.88"
MQTT_PORT = 1883
MQTT_TOPIC = "smartgreengarden/sensor/data"

# === Menyimpan data sensor terakhir ===
latest_data = {}

# === Kirim pesan ke Telegram (Thread-safe) ===
def send_to_telegram(message):
    def send():
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code != 200:
                print("❌ Gagal kirim ke Telegram:", response.text)
        except Exception as e:
            print("❌ Error Telegram:", str(e))
    
    with ThreadPoolExecutor() as executor:
        executor.submit(send)

# === Kirim semua data sensor secara otomatis ===
def auto_send_all_sensor_data():
    while True:
        if latest_data:
            message = "<b>⏰ UPDATE DATA SENSOR TERBARU</b>\n"
            message += f"⏱️ {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            for key, value in latest_data.items():
                # Tangani nilai NaN
                if "nan" in value.lower():
                    value = value.replace("nan", "0.0")
                    latest_data[key] = value  # Update nilai di cache
                message += f"• <b>{key}</b>: {value}\n"
            send_to_telegram(message)
        time.sleep(300)  # Kirim setiap 5 menit

# === Fungsi handle command dari user ===
def handle_command(command):
    command = command.strip()
    
    if command == "/help":
        help_text = (
            "<b>📋 DAFTAR PERINTAH</b>\n\n"
            "<b>🔄 DATA SENSOR</b>\n"
            "<code>/tds1</code> - TDS Sensor 1\n"
            "<code>/tds2</code> - TDS Sensor 2\n"
            "<code>/turbidity1</code> - Turbidity 1\n"
            "<code>/turbidity2</code> - Turbidity 2\n"
            "<code>/flowrate</code> - Flow Rate\n"
            "<code>/total_litres</code> - Total Liter\n"
            "<code>/level1</code> - Level Sensor 1\n"
            "<code>/level2</code> - Level Sensor 2\n"
            "<code>/level3</code> - Level Sensor 3\n"
            "<code>/level4</code> - Level Sensor 4\n"
            "<code>/all_data</code> - Semua data\n\n"
            "<b>⚙️ KALIBRASI</b>\n"
            "<code>/cal_tds1:[nilai]</code> - Kalibrasi TDS1\n"
            "<code>/cal_tds2:[nilai]</code> - Kalibrasi TDS2"
        )
        return help_text

    elif command == "/all_data":
        if not latest_data:
            return "⚠️ Data sensor belum tersedia."
        
        response = "<b>📊 DATA SENSOR TERKINI</b>\n"
        response += f"⏱️ {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        for key, value in latest_data.items():
            # Tangani nilai NaN
            if "nan" in value.lower():
                value = value.replace("nan", "0.0")
            response += f"• <b>{key}</b>: {value}\n"
        return response
    
    elif command.startswith("/cal_tds1:"):
        try:
            tds_value = float(command.split(":")[1])
            mqtt_client.publish("smartgreengarden/sensor/kalibrasi/tds1", str(tds_value))
            return f"✅ Perintah kalibrasi TDS1 dikirim: {tds_value} ppm"
        except:
            return "❌ Format: /cal_tds1:[nilai_ppm]"
    
    elif command.startswith("/cal_tds2:"):
        try:
            tds_value = float(command.split(":")[1])
            mqtt_client.publish("smartgreengarden/sensor/kalibrasi/tds2", str(tds_value))
            return f"✅ Perintah kalibrasi TDS2 dikirim: {tds_value} ppm"
        except:
            return "❌ Format: /cal_tds2:[nilai_ppm]"
    
    else:
        key_map = {
            "/tds1": "tds1",
            "/tds2": "tds2",
            "/turbidity1": "turbidity1",
            "/turbidity2": "turbidity2",
            "/flowrate": "flowrate",
            "/total_litres": "totalflow",
            "/level1": "level1",
            "/level2": "level2",
            "/level3": "level3",
            "/level4": "level4"
        }
        
        if command in key_map:
            key = key_map[command]
            if key in latest_data:
                value = latest_data[key]
                # Tangani nilai NaN
                if "nan" in value.lower():
                    value = value.replace("nan", "0.0")
                return f"<b>{key.upper()}</b>: {value}"
            else:
                return "⚠️ Data belum tersedia"
        else:
            return "❌ Perintah tidak dikenali. Gunakan /help"

# === Polling update dari Telegram ===
def telegram_polling_loop():
    print("📲 Memulai polling Telegram...")
    offset = 0
    
    while True:
        try:
            url = f"{TELEGRAM_API_URL}/getUpdates"
            params = {'offset': offset, 'timeout': 30}
            response = requests.get(url, params=params, timeout=60)
            data = response.json()
            
            if "result" in data:
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = str(msg["chat"]["id"])
                        text = msg.get("text", "").strip()
                        
                        if chat_id == TELEGRAM_CHAT_ID and text.startswith("/"):
                            response = handle_command(text)
                            send_to_telegram(response)
        except Exception as e:
            print("❌ Error Telegram polling:", str(e))
            time.sleep(5)

# === MQTT Callback ===
def on_connect(client, userdata, flags, rc):
    print("✅ Terhubung ke MQTT Broker")
    client.subscribe(MQTT_TOPIC)

# def on_message(client, userdata, msg):
#     try:
#         topic = msg.topic.split("/")[-1]
#         payload = msg.payload.decode()
        
#         # Tangani nilai NaN dari MQTT
#         if "nan" in payload.lower():
#             payload = payload.replace("nan", "0.0")
#             print(f"⚠️ NaN ditemukan di {topic}, diganti dengan 0.0")
        
#         latest_data[topic] = payload
#         print(f"📩 [MQTT] {topic}: {payload}")
#     except Exception as e:
#         print("❌ Error MQTT:", str(e))

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        
        # Tangani nilai NaN
        if "nan" in payload.lower():
            payload = payload.replace("nan", "0.0")
            print("⚠️ NaN ditemukan, diganti dengan 0.0")
        
        # Jika topik adalah sensor/data → parse JSON
        if msg.topic == "smartgreengarden/sensor/data":
            data = json.loads(payload)
            for key, value in data.items():
                latest_data[key.lower()] = str(value)
            print(f"📩 [MQTT] Data sensor diperbarui: {latest_data}")
        else:
            latest_data[msg.topic] = payload
            print(f"📩 [MQTT] {msg.topic}: {payload}")
    except Exception as e:
        print("❌ Error MQTT:", str(e))

# === Main Program ===
if __name__ == "__main__":
    # === Inisialisasi MQTT Client ===
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # === Kirim notifikasi aktif ===
    send_to_telegram("✅ <b>SMART GREEN GARDEN BOT AKTIF</b>\nSistem monitoring siap menerima perintah!")

    # === Jalankan thread ===
    threads = [
        threading.Thread(target=mqtt_client.loop_forever),
        threading.Thread(target=telegram_polling_loop),
        threading.Thread(target=auto_send_all_sensor_data)
    ]
    
    for t in threads:
        t.daemon = True
        t.start()
    
    for t in threads:
        t.join()