import paho.mqtt.client as mqtt
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import logging

# === Konfigurasi ===
TELEGRAM_BOT_TOKEN = '7744245206:AAHGAlfLOK3F3ECSpVHSEQJIfxDay4qT5fo'
TELEGRAM_CHAT_ID = '5344109406'
MQTT_BROKER = '192.168.25.1'
MQTT_PORT = 1883
MQTT_TOPIC_CALIB = 'smartgreengarden/kalibrasi/tds'
MQTT_TOPIC_RESPONSE = 'smartgreengarden/kalibrasi/response'

# === Logging ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === Global variabel untuk bot dan application ===
application = None
bot = None

# === MQTT Callback ===
def on_connect(client, userdata, flags, rc):
    print("✅ MQTT Connected with result code " + str(rc))
    client.subscribe(MQTT_TOPIC_RESPONSE)

def on_message(client, userdata, msg):
    response = msg.payload.decode()
    print("📩 Dari ESP32:", response)
    # Kirim ke Telegram
    if bot:
        asyncio.run(bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=response))

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)

# === Command handler ===
async def cal_tds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❗ Format salah. Gunakan /calTDS <nilai_ppm>")
        return
    try:
        tds_value = float(context.args[0])
        mqtt_client.publish(MQTT_TOPIC_CALIB, str(tds_value))
        await update.message.reply_text(f"📤 Mengirim nilai kalibrasi: {tds_value} ppm")
    except ValueError:
        await update.message.reply_text("❌ Harus berupa angka. Contoh: /calTDS 520")

# === Main function ===
async def main():
    global bot, application

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    bot = application.bot

    application.add_handler(CommandHandler("calTDS", cal_tds))

    print("🤖 Bot Telegram siap. Kirim /calTDS <nilai>")
    await application.run_polling()

# === Jalankan MQTT dan Telegram Bot secara paralel ===
import threading

mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
mqtt_thread.start()

asyncio.run(main())
