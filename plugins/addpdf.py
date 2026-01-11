from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS, STORAGE_CHANNEL_ID
from database import pdfs

user_step = {}


# ===================== /addpdf =====================
@Client.on_message(filters.command("addpdf") & filters.user(ADMINS))
async def add_pdf(client, message):
    exams = await pdfs.distinct("exam")

    buttons = [[InlineKeyboardButton(e, callback_data=f"add_e|{e}")] for e in exams]
    buttons.append([InlineKeyboardButton("➕ New Exam", callback_data="add_e|NEW")])

    user_step[message.from_user.id] = {}

    await message.reply_text(
        "📘 **Select Exam**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ===================== EXAM =====================
@Client.on_callback_query(filters.regex("^add_e\\|"))
async def add_exam(client, cb):
    await cb.answer()
    uid = cb.from_user.id
    choice = cb.data.split("|")[1]

    if choice == "NEW":
        user_step[uid]["step"] = "exam"
        await cb.message.edit_text("✍️ Send New Exam Name")
    else:
        user_step[uid]["exam"] = choice
        await show_subjects(cb.message)


# ===================== SUBJECT =====================
async def show_subjects(message):
    uid = message.from_user.id
    exam = user_step[uid]["exam"]

    subs = await pdfs.distinct("subject", {"exam": exam})
    buttons = [[InlineKeyboardButton(s, callback_data=f"add_s|{s}")] for s in subs]
    buttons.append([InlineKeyboardButton("➕ New Subject", callback_data="add_s|NEW")])

    await message.reply_text(
        "📗 **Select Subject**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^add_s\\|"))
async def add_subject(client, cb):
    await cb.answer()
    uid = cb.from_user.id
    choice = cb.data.split("|")[1]

    if choice == "NEW":
        user_step[uid]["step"] = "subject"
        await cb.message.edit_text("✍️ Send New Subject Name")
    else:
        user_step[uid]["subject"] = choice
        await show_topics(cb.message)


# ===================== TOPIC =====================
async def show_topics(message):
    uid = message.from_user.id
    exam = user_step[uid]["exam"]
    subject = user_step[uid]["subject"]

    topics = await pdfs.distinct("topic", {"exam": exam, "subject": subject})
    buttons = [[InlineKeyboardButton(t, callback_data=f"add_t|{t}")] for t in topics]
    buttons.append([InlineKeyboardButton("➕ New Topic", callback_data="add_t|NEW")])

    await message.reply_text(
        "📙 **Select Topic**",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^add_t\\|"))
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
        await cb.message.edit_text(
            "📤 **Upload Mode**\n\n"
            "• Send Image (optional)\n"
            "• Then send PDF\n\n"
            "You can repeat Image → PDF multiple times"
        )


# ===================== TEXT INPUT (NEW EXAM / SUBJECT / TOPIC) =====================
@Client.on_message(filters.text & ~filters.command & filters.user(ADMINS))
async def save_text(client, message):
    uid = message.from_user.id

    if uid not in user_step or "step" not in user_step[uid]:
        return

    step = user_step[uid]["step"]
    value = message.text.strip()

    user_step[uid][step] = value
    user_step[uid].pop("step")

    await message.reply_text("✅ Saved")

    if step == "exam":
        await show_subjects(message)
    elif step == "subject":
        await show_topics(message)
    elif step == "topic":
        user_step[uid]["step"] = "upload"
        await message.reply_text(
            "📤 **Upload Mode**\n\n"
            "• Send Image (optional)\n"
            "• Then send PDF"
        )


# ===================== IMAGE (OPTIONAL) =====================
@Client.on_message(filters.photo & filters.user(ADMINS))
async def save_image(client, message):
    uid = message.from_user.id
    if uid not in user_step:
        return
    if user_step[uid].get("step") != "upload":
        return

    user_step[uid]["last_image"] = message.photo.file_id


# ===================== PDF UPLOAD =====================
@Client.on_message(filters.document & filters.user(ADMINS))
async def save_pdf(client, message):
    uid = message.from_user.id
    if uid not in user_step:
        return
    if user_step[uid].get("step") != "upload":
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

    await message.reply_text("✅ **PDF Stored Successfully**")
