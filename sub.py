import paho.mqtt.client as mqtt
import mysql.connector
import json
from telegram import Bot

# 🔹 MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="sensor-iot_db"
)
cursor = db.cursor()

# 🔹 MQTT Setup
BROKER = "192.168.21.44"
TOPIC_DATA = "sensor/waterlevel"          
TOPIC_REQUEST = "request/waterlevel"      
TOPIC_RESPONSE = "response/waterlevel"    

# 🔹 Telegram Bot Setup
TELEGRAM_BOT_TOKEN = "7744245206:AAHGAlfLOK3F3ECSpVHSEQJIfxDay4qT5fo"
CHAT_ID = "5344109406"
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# 🔹 MQTT Callback
def on_message(client, userdata, msg):
    topic = msg.topic

    try:
        if topic == TOPIC_DATA:
            # Data dari sensor
            data = json.loads(msg.payload)
            sensor_value = data["sensor_value"]
            status = data["status"]
            print(f"📩 Received Sensor Data: {sensor_value}, Status: {status}")

            # Simpan ke database
            sql = "INSERT INTO waterlevel (sensor_value, status) VALUES (%s, %s)"
            cursor.execute(sql, (sensor_value, status))
            db.commit()
            print("✅ Data inserted into MySQL")

            # Kirim notifikasi ke Telegram
            bot.send_message(chat_id=CHAT_ID, text=f"📩 New Sensor Data:\n• Value: {sensor_value}\n• Status: {status}")

        elif topic == TOPIC_REQUEST:
            print("📥 Permintaan data dari BOT diterima...")

            # Ambil data terbaru dari database
            cursor.execute("SELECT sensor_value, status FROM waterlevel ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()

            if result:
                sensor_value, status = result
                response = {
                    "sensor_value": sensor_value,
                    "status": status
                }
                client.publish(TOPIC_RESPONSE, json.dumps(response))
                print("📤 Response terkirim ke bot:", response)
            else:
                print("⚠️ Tidak ada data di database.")

    except Exception as e:
        print("❌ Error:", e)

# 🔹 MQTT Init
client = mqtt.Client()
client.connect(BROKER, 1883, 60)
client.subscribe([(TOPIC_DATA, 0), (TOPIC_REQUEST, 0)])  # subscribe ke 2 topik
client.on_message = on_message

print("🔄 Subscriber listening for MQTT messages...")
client.loop_forever()
