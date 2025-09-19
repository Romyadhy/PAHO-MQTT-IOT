import asyncio
import paho.mqtt.client as mqtt
from telegram import Bot
from telegram.error import TelegramError

# === KONFIGURASI ===
MQTT_BROKER = "192.168.25.1"
MQTT_PORT = 1883

BOT_TOKEN = "7744245206:AAHGAlfLOK3F3ECSpVHSEQJIfxDay4qT5fo"
CHAT_ID = "5344109406"

# Inisialisasi bot telegram
bot = Bot(token=BOT_TOKEN)

# Queue untuk komunikasi antara MQTT dan Telegram
message_queue = asyncio.Queue()

# === Fungsi kirim ke Telegram (ASYNC) ===
async def telegram_worker():
    while True:
        message = await message_queue.get()
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message)
            print(f"📤 Terkirim ke Telegram: {message}")
        except TelegramError as e:
            print(f"❌ Gagal kirim ke Telegram: {e}")
        message_queue.task_done()

# === Callback MQTT ===
def on_connect(client, userdata, flags, rc):
    print("🔌 MQTT Connected with code:", rc)
    client.subscribe("smartgreengarden/sensors/tds1")
    client.subscribe("smartgreengarden/sensors/tds2")
    client.subscribe("smartgreengarden/sensors/tds1/kalibrasi")
    client.subscribe("smartgreengarden/sensors/tds2/kalibrasi")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    print(f"📥 MQTT | Topic: {topic} | Payload: {payload}")

    # Format pesan berdasarkan topic
    if topic == "smartgreengarden/sensors/tds1":
        asyncio.run_coroutine_threadsafe(message_queue.put(f"📡 Update TDS1: {payload}"), loop)
    elif topic == "smartgreengarden/sensors/tds2":
        asyncio.run_coroutine_threadsafe(message_queue.put(f"📡 Update TDS2: {payload}"), loop)
    elif topic == "smartgreengarden/sensors/tds1/kalibrasi":
        asyncio.run_coroutine_threadsafe(message_queue.put(f"🛠️ Kalibrasi TDS1: {payload}"), loop)
    elif topic == "smartgreengarden/sensors/tds2/kalibrasi":
        asyncio.run_coroutine_threadsafe(message_queue.put(f"🛠️ Kalibrasi TDS2: {payload}"), loop)

# === Main Async Function ===
async def main():
    global loop
    loop = asyncio.get_running_loop()

    # Mulai worker telegram
    asyncio.create_task(telegram_worker())

    # Setup MQTT Client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("🔄 Menghubungkan ke MQTT broker...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # Jalankan MQTT di thread terpisah
    client.loop_start()

    # Biar asyncio jalan terus
    while True:
        await asyncio.sleep(1)

# Jalankan
if __name__ == "__main__":
    asyncio.run(main())
