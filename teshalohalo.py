import paho.mqtt.client as mqtt
import requests
import time
import threading

# === Konfigurasi Telegram ===
TELEGRAM_BOT_TOKEN = '7744245206:AAHGAlfLOK3F3ECSpVHSEQJIfxDay4qT5fo'
TELEGRAM_CHAT_ID = '5344109406'
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# === Konfigurasi MQTT ===
MQTT_BROKER = "192.168.21.210"
MQTT_PORT = 1883
MQTT_TOPIC = "smartgreengarden/monitoring/sensors/#"

# === Menyimpan data sensor terakhir ===
latest_data = {}

# === Kirim pesan ke Telegram ===
def send_to_telegram(message):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print("❌ Gagal kirim ke Telegram:", response.text)

# === Kirim semua data sensor secara otomatis tiap 5 menit ===
def auto_send_all_sensor_data():
    while True:
        if latest_data:
            message = "<b>⏰ Update Berkala: Semua Data Sensor</b>\n"
            for key, value in latest_data.items():
                message += f"<b>{key}</b>: <code>{value}</code>\n"
            send_to_telegram(message)
        else:
            send_to_telegram("⚠️ Belum ada data sensor untuk dikirim otomatis.")
        time.sleep(300)  # 5 menit

# === Fungsi handle command dari user ===
def handle_command(command):
    if command == "/help":
        help_text = (
            "<b>📋 Daftar Perintah:</b>\n"
            "<code>/tds1</code> - TDS Sensor 1\n"
            "<code>/tds2</code> - TDS Sensor 2\n"
            "<code>/turbidity1</code> - Turbidity Sensor 1\n"
            "<code>/turbidity2</code> - Turbidity Sensor 2\n"
            "<code>/flowrate</code> - Flow Rate\n"
            "<code>/total_litres</code> - Total Liter\n"
            "<code>/level1</code> hingga <code>/level4</code> - Status Water Level\n"
            "<code>/allsensor-data</code> - Tampilkan semua data sensor"
        )
        return help_text

    elif command == "/allsensor-data":
        if not latest_data:
            return "⚠️ Data sensor belum tersedia."
        
        all_data_text = "<b>📊 Semua Data Sensor:</b>\n"
        for key, value in latest_data.items():
            all_data_text += f"<b>{key}</b>: <code>{value}</code>\n"
        return all_data_text
    
    # tdscalibrations
    elif command.startswith("/calTDS:"):
        try:
            tds_value = int(command.split(":")[1])
            mqtt_client.publish("smartgreengarden/kalibrasi/tds", tds_value)
            return f"✅ Kalibrasi TDS dikirim ke perangkat: {tds_value} ppm"
        except:
            return "❌ Format salah. Gunakan: /calTDS:<angka>"

    else:
        key = command.strip("/").lower()
        if key in latest_data:
            return f"<b>{key}</b>: <code>{latest_data[key]}</code>"
        else:
            return "❗ Data tidak ditemukan atau belum tersedia."

# === Polling update dari Telegram ===
def get_updates(offset=None):
    url = f"{TELEGRAM_API_URL}/getUpdates"
    params = {'timeout': 100, 'offset': offset}
    response = requests.get(url, params=params)
    return response.json()

def process_updates(updates):
    for update in updates.get("result", []):
        update_id = update["update_id"]
        if "message" in update:
            msg = update["message"]
            chat_id = str(msg["chat"]["id"])
            text = msg.get("text", "")
            if chat_id == TELEGRAM_CHAT_ID and text.startswith("/"):
                response = handle_command(text)
                send_to_telegram(response)
        yield update_id + 1

def telegram_polling_loop():
    print("📲 Memulai polling Telegram...")
    offset = None
    while True:
        updates = get_updates(offset)
        new_offset = None
        for new_offset in process_updates(updates):
            pass
        offset = new_offset
        time.sleep(2)

# === MQTT Callback ===
def on_connect(client, userdata, flags, rc):
    print("✅ Terhubung ke MQTT Broker dengan kode:", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        topic = msg.topic.replace("smartgreengarden/monitoring/sensors/", "")
        latest_data[topic] = payload
        print(f"📩 [{topic}] = {payload}")
    except Exception as e:
        print("❌ Error saat parsing MQTT:", e)

# === Inisialisasi MQTT Client ===
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# === Kirim notifikasi awal bahwa bot aktif ===
send_to_telegram("✅ <b>BOTMON AKTIF!!</b>\nGunakan <code>/help</code> untuk melihat daftar perintah.")

# === Jalankan MQTT, Telegram polling, dan pengiriman otomatis ===
mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
telegram_thread = threading.Thread(target=telegram_polling_loop)
auto_send_thread = threading.Thread(target=auto_send_all_sensor_data)

mqtt_thread.start()
telegram_thread.start()
auto_send_thread.start()
