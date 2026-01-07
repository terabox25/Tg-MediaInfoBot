from pyrogram import Client, filters
from config import API_ID, API_HASH, BOT_TOKEN
import os

app = Client(
    "pdf_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

@app.on_message(filters.command("start"))
async def start(_, m):
    await m.reply(
        "📚 Coaching PDF Bot\n\n"
        "Use /pdf to get study material"
    )

app.run()
