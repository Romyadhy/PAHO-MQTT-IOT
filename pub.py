import asyncio
import json
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# MQTT Setup
BROKER = "192.168.21.44"
PORT = 1883
TOPIC_COMMAND = "request/waterlevel"
TOPIC_RESPONSE = "response/waterlevel"

# Global data untuk menyimpan response sementara
latest_response = None

# MQTT client
mqtt_client = mqtt.Client()

def on_message(client, userdata, msg):
    global latest_response
    try:
        if msg.topic == TOPIC_RESPONSE:
            data = json.loads(msg.payload)
            latest_response = data
            print("📥 Response diterima dari subscriber")
    except Exception as e:
        print("❌ Error parsing response:", e)

# Connect dan subscribe
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, PORT, 60)
mqtt_client.subscribe(TOPIC_RESPONSE)
mqtt_client.loop_start()

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome! Use /send <command> or /waterlevel to get data.")

async def send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a command. Example: /send LED_ON")
        return

    command = " ".join(context.args)
    print(f"📤 Sending command: {command}")
    mqtt_client.publish("sensor/waterlevel", command)
    await update.message.reply_text(f"📤 Command sent: {command}")

# ✅ Handler khusus untuk waterlevel
async def waterlevel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global latest_response
    latest_response = None  # reset response

    # Publish permintaan data ke subscriber
    mqtt_client.publish(TOPIC_COMMAND, "GET")
    print("📤 Requesting water level...")

    # Tunggu respons selama 2 detik
    for i in range(10):
        await asyncio.sleep(0.2)
        if latest_response is not None:
            break

    # Balas ke user
    if latest_response:
        sensor_value = latest_response.get("sensor_value", "-")
        status = latest_response.get("status", "-")
        await update.message.reply_text(f"📊 Water Level:\n• Value: {sensor_value}\n• Status: {status}")
    else:
        await update.message.reply_text("⚠️ Tidak ada respon dari sensor.")

# Main Function
def main():
    TELEGRAM_BOT_TOKEN = "7744245206:AAHGAlfLOK3F3ECSpVHSEQJIfxDay4qT5fo"

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send))
    app.add_handler(CommandHandler("waterlevel", waterlevel))

    print("🤖 Telegram bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
