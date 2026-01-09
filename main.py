from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN

app = Client(
    "pdf_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins")
)

START_IMAGE = "https://i.imgur.com/tJwBpHo.jpeg"  
# ⬆️ yaha apni image ka direct link lagao

ADMIN_USERNAME = "lkd_ak"
CHANNEL_LINK = "https://t.me/How_To_Google"

@app.on_message(filters.command("start"))
async def start(_, m):
    await m.reply_photo(
        photo=START_IMAGE,
        caption=(
            "📚 **Coaching PDF Bot**\n\n"
            "Is bot ki madad se aap coaching ke **study PDFs** "
            "asani se download kar sakte hain.\n\n"

            "🧭 **Bot Use Karne Ka Tarika:**\n"
            "➡️ `/pdf` – Subject / topic wise PDFs paane ke liye\n"
            "➡️ **Search Feature** – Koi bhi topic ka naam likhkar bheje\n\n"

            "🔍 **Search Kaise Kare?**\n"
            "Sirf topic ka naam likhe jaise:\n"
            "`Indian Polity Notes`\n"
            "`History PDF`\n\n"
            "Agar related PDF available hogi to bot turant dikha dega, "
            "nahi hogi to inform karega.\n\n"

            "👇 Zaroori Links Neeche Diye Gaye Hain"
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📞 Contact Admin",
                        url=f"https://t.me/{ADMIN_USERNAME}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📢 Join Channel",
                        url=CHANNEL_LINK
                    )
                ]
            ]
        )
    )
