import asyncio
import paho.mqtt.client as mqtt
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
import sys

# === KONFIGURASI ===
MQTT_BROKER = "192.168.28.141"
MQTT_PORT = 1883

BOT_TOKEN = "7744245206:AAHGAlfLOK3F3ECSpVHSEQJIfxDay4qT5fo"
CHAT_ID = "5344109406"

# === Variabel Global ===
tds_data = {"tds1": None, "tds2": None}
message_queue = asyncio.Queue()
main_loop = None  # Tambahan: simpan event loop utama


# === Fungsi Worker untuk mengirim ke Telegram ===
async def telegram_worker():
    bot = Bot(token=BOT_TOKEN)
    while True:
        message = await message_queue.get()
        try:
            await bot.send_message(chat_id=CHAT_ID, text=message)
            print(f"📤 Terkirim ke Telegram: {message}")
        except TelegramError as e:
            print(f"❌ Gagal kirim ke Telegram: {e}")
        message_queue.task_done()


# === Fungsi Worker untuk mengirim ke Telegram secara periodik ===
async def periodic_telegram_worker():
    bot = Bot(token=BOT_TOKEN)
    last_sent = None
    while True:
        # Kirim data setiap 5 detik jika data sudah ada
        if tds_data["tds1"] is not None and tds_data["tds2"] is not None:
            message = f"📊 Data TDS Update (periodik):\nTDS1: {tds_data['tds1']}\nTDS2: {tds_data['tds2']}"
            try:
                await bot.send_message(chat_id=CHAT_ID, text=message)
                print(f"📤 Terkirim ke Telegram (periodik): {message}")
            except TelegramError as e:
                print(f"❌ Gagal kirim ke Telegram (periodik): {e}")
        await asyncio.sleep(5)


# === Callback MQTT ===
def on_connect(client, userdata, flags, rc):
    print("🔌 MQTT Connected with code:", rc)
    client.subscribe("smartgreengarden/sensors/tds1")
    client.subscribe("smartgreengarden/sensors/tds2")


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    print(f"📥 MQTT | Topic: {topic} | Payload: {payload}")

    if topic == "smartgreengarden/sensors/tds1":
        tds_data["tds1"] = payload
    elif topic == "smartgreengarden/sensors/tds2":
        tds_data["tds2"] = payload

    if tds_data["tds1"] is not None and tds_data["tds2"] is not None:
        # Tidak perlu kirim ke Telegram di sini, cukup update data
        pass


# === Handler perintah kalibrasi ===
async def cal_tds1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mqtt_client.publish("smartgreengarden/sensors/tds1/kalibrasi", "kalibrasi_tds1")
    await update.message.reply_text("⚙️ Kalibrasi TDS1 dikirim!")


async def cal_tds2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mqtt_client.publish("smartgreengarden/sensors/tds2/kalibrasi", "kalibrasi_tds2")
    await update.message.reply_text("⚙️ Kalibrasi TDS2 dikirim!")


# Handler untuk /tds1 dan /tds2
async def tds1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = tds_data["tds1"]
    if value is not None:
        await update.message.reply_text(f"TDS1: {value}")
    else:
        await update.message.reply_text("Data TDS1 belum tersedia.")

async def tds2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = tds_data["tds2"]
    if value is not None:
        await update.message.reply_text(f"TDS2: {value}")
    else:
        await update.message.reply_text("Data TDS2 belum tersedia.")


# === Fungsi Utama ===
async def main():
    global mqtt_client, main_loop
    main_loop = asyncio.get_running_loop()  # Simpan event loop utama

    # === Start worker Telegram ===
    asyncio.create_task(telegram_worker())
    # === Start worker Telegram periodik ===
    asyncio.create_task(periodic_telegram_worker())

    # === MQTT Setup ===
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()

    # === Bot Telegram Setup ===
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("calTDS1", cal_tds1))
    app.add_handler(CommandHandler("calTDS2", cal_tds2))
    app.add_handler(CommandHandler("tds1", tds1_handler))
    app.add_handler(CommandHandler("tds2", tds2_handler))

    print("🚀 Bot Telegram & MQTT siap digunakan.")
    await app.run_polling()


# === Start Program ===
if __name__ == "__main__":
    import sys
    if sys.platform.startswith("win") and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    import nest_asyncio
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
