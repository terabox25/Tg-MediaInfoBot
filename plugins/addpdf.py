from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS, STORAGE_CHANNEL_ID
from database import pdfs

user_step = {}


# ───────────── START ADD PDF ─────────────
@Client.on_message(filters.command("addpdf") & filters.user(ADMINS))
async def add_pdf(client, message):
    user_step[message.from_user.id] = {}

    exams = await pdfs.distinct("exam")
    buttons = [[InlineKeyboardButton(e, callback_data=f"add_e|{e}")] for e in exams]
    buttons.append([InlineKeyboardButton("➕ New Exam", callback_data="add_e|NEW")])

    await message.reply_text(
        "📘 Select Exam",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ───────────── EXAM CALLBACK ─────────────
@Client.on_callback_query(filters.regex("^add_e"))
async def add_exam(client, cb):
    await cb.answer()
    uid = cb.from_user.id
    choice = cb.data.split("|")[1]

    if uid not in user_step:
        user_step[uid] = {}

    if choice == "NEW":
        user_step[uid]["step"] = "exam"
        await cb.message.edit_text("✍️ Send New Exam Name")
    else:
        user_step[uid]["exam"] = choice
        await show_subjects(cb.message, uid)


# ───────────── SUBJECT MENU ─────────────
async def show_subjects(msg, uid):
    exam = user_step[uid].get("exam")
    if not exam:
        return

    subs = await pdfs.distinct("subject", {"exam": exam})
    buttons = [[InlineKeyboardButton(s, callback_data=f"add_s|{s}")] for s in subs]
    buttons.append([InlineKeyboardButton("➕ New Subject", callback_data="add_s|NEW")])

    await msg.edit_text(
        "📗 Select Subject",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^add_s"))
async def add_subject(client, cb):
    await cb.answer()
    uid = cb.from_user.id
    choice = cb.data.split("|")[1]

    if choice == "NEW":
        user_step[uid]["step"] = "subject"
        await cb.message.edit_text("✍️ Send New Subject Name")
    else:
        user_step[uid]["subject"] = choice
        await show_topics(cb.message, uid)


# ───────────── TOPIC MENU ─────────────
async def show_topics(msg, uid):
    exam = user_step[uid]["exam"]
    subject = user_step[uid]["subject"]

    topics = await pdfs.distinct("topic", {"exam": exam, "subject": subject})
    buttons = [[InlineKeyboardButton(t, callback_data=f"add_t|{t}")] for t in topics]
    buttons.append([InlineKeyboardButton("➕ New Topic", callback_data="add_t|NEW")])

    await msg.edit_text(
        "📙 Select Topic",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^add_t"))
async def add_topic(client, cb):
    await cb.answer()
    uid = cb.from_user.id
    choice = cb.data.split("|")[1]

    if choice == "NEW":
        user_step[uid]["step"] = "topic"
        await cb.message.edit_text("✍️ Send New Topic Name")
    else:
        user_step[uid]["topic"] = choice
        user_step[uid]["step"] = "upload"
        await cb.message.edit_text("📤 Send Image (optional) then PDF")


# ───────────── SAVE TEXT INPUT ─────────────
@Client.on_message(filters.text & filters.user(ADMINS))
async def save_text(client, message):
    if message.text.startswith("/"):
        return

    uid = message.from_user.id
    if uid not in user_step or "step" not in user_step[uid]:
        return

    step = user_step[uid]["step"]
    user_step[uid][step] = message.text.strip()
    user_step[uid].pop("step")

    if step == "exam":
        await show_subjects(message, uid)
    elif step == "subject":
        await show_topics(message, uid)
    elif step == "topic":
        user_step[uid]["step"] = "upload"
        await message.reply_text("📤 Upload Image (optional) then PDF")


# ───────────── IMAGE ─────────────
@Client.on_message(filters.photo & filters.user(ADMINS))
async def save_image(client, message):
    uid = message.from_user.id
    if user_step.get(uid, {}).get("step") != "upload":
        return

    user_step[uid]["last_image"] = message.photo.file_id


# ───────────── PDF ─────────────
@Client.on_message(filters.document & filters.user(ADMINS))
async def save_pdf(client, message):
    uid = message.from_user.id
    if user_step.get(uid, {}).get("step") != "upload":
        return

    fwd = await message.forward(STORAGE_CHANNEL_ID)

    data = {
        "exam": user_step[uid]["exam"],
        "subject": user_step[uid]["subject"],
        "topic": user_step[uid]["topic"],
        "file_id": fwd.document.file_id,
        "file_name": fwd.document.file_name
    }

    if user_step[uid].get("last_image"):
        data["cover_id"] = user_step[uid]["last_image"]

    await pdfs.insert_one(data)
    user_step[uid]["last_image"] = None

    await message.reply("✅ PDF Saved")
