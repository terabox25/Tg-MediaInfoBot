from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS, STORAGE_CHANNEL_ID
from database import pdfs

user_step = {}

@filters.user(ADMINS)
async def admin_only(_, __):
    return True

@filters.private
async def private_only(_, __):
    return True

@filters.user(ADMINS) & filters.command("addpdf")
async def addpdf(client, message):
    user_step[message.from_user.id] = {"step": "exam"}
    await message.reply(
        "📂 Select Exam",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("SSC", callback_data="exam_SSC")],
            [InlineKeyboardButton("UPSC", callback_data="exam_UPSC")]
        ])
    )

@filters.callback_query
async def callbacks(client, cb):
    uid = cb.from_user.id
    data = cb.data

    if uid not in user_step:
        return

    step = user_step[uid]["step"]

    if step == "exam":
        user_step[uid]["exam"] = data.split("_")[1]
        user_step[uid]["step"] = "subject"
        await cb.message.edit(
            "📘 Select Subject",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("History", callback_data="sub_History")],
                [InlineKeyboardButton("Polity", callback_data="sub_Polity")]
            ])
        )

    elif step == "subject":
        user_step[uid]["subject"] = data.split("_")[1]
        user_step[uid]["step"] = "topic"
        await cb.message.edit(
            "📗 Select Topic",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Modern", callback_data="top_Modern")],
                [InlineKeyboardButton("Ancient", callback_data="top_Ancient")]
            ])
        )

    elif step == "topic":
        user_step[uid]["topic"] = data.split("_")[1]
        user_step[uid]["step"] = "pdf"
        await cb.message.edit("📄 Now send PDF file")

@filters.user(ADMINS) & filters.document
async def save_pdf(client, message):
    uid = message.from_user.id
    if uid not in user_step or user_step[uid]["step"] != "pdf":
        return

    fwd = await message.forward(STORAGE_CHANNEL_ID)

    data = {
        "exam": user_step[uid]["exam"],
        "subject": user_step[uid]["subject"],
        "topic": user_step[uid]["topic"],
        "file_id": fwd.document.file_id,
        "file_name": fwd.document.file_name
    }

    await pdfs.insert_one(data)
    user_step.pop(uid)

    await message.reply("✅ PDF Stored Successfully")
