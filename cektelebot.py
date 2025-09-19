import asyncio
from telegram import Bot

BOT_TOKEN = "7744245206:AAHGAlfLOK3F3ECSpVHSEQJIfxDay4qT5fo"
CHAT_ID = "5344109406"

bot = Bot(token=BOT_TOKEN)

async def send_test_message():
    await bot.send_message(chat_id=CHAT_ID, text="🚀 Test kirim pesan dari Python")

# Jalankan event loop
asyncio.run(send_test_message())
