from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS, STORAGE_CHANNEL_ID
from database import pdfs

user_step = {}

@Client.on_message(filters.command("addpdf") & filters.user(ADMINS))
async def addpdf(client, message):
    user_step[message.from_user.id] = {"step": "exam"}
    await message.reply(
        "📂 Select Exam",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("SSC", callback_data="exam_SSC")],
            [InlineKeyboardButton("UPSC", callback_data="exam_UPSC")]
        ])
    )

@Client.on_callback_query()
async def callback_handler(client, cb):
    uid = cb.from_user.id
    if uid not in user_step:
        return

    data = cb.data
    step = user_step[uid].get("step")

    if step == "exam" and data.startswith("exam_"):
        user_step[uid]["exam"] = data.split("_")[1]
        user_step[uid]["step"] = "subject"
        await cb.message.edit(
            "📘 Select Subject",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("History", callback_data="sub_History")],
                [InlineKeyboardButton("Polity", callback_data="sub_Polity")]
            ])
        )

    elif step == "subject" and data.startswith("sub_"):
        user_step[uid]["subject"] = data.split("_")[1]
        user_step[uid]["step"] = "topic"
        await cb.message.edit(
            "📗 Select Topic",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Modern", callback_data="top_Modern")],
                [InlineKeyboardButton("Ancient", callback_data="top_Ancient")]
            ])
        )

    elif step == "topic" and data.startswith("top_"):
        user_step[uid]["topic"] = data.split("_")[1]
        user_step[uid]["step"] = "pdf"
        await cb.message.edit("📄 Now send PDF file")

@Client.on_message(filters.document & filters.user(ADMINS))
async def save_pdf(client, message):
    uid = message.from_user.id

    # 🔒 MAIN FIX (crash stopper)
    if uid not in user_step:
        return
    if user_step[uid].get("step") != "pdf":
        return

    fwd = await message.forward(STORAGE_CHANNEL_ID)

    await pdfs.insert_one({
        "exam": user_step[uid]["exam"],
        "subject": user_step[uid]["subject"],
        "topic": user_step[uid]["topic"],
        "file_id": fwd.document.file_id,
        "file_name": fwd.document.file_name
    })

    # 🔒 SAFE POP
    user_step.pop(uid, None)

    await message.reply("✅ PDF Stored Successfully")
