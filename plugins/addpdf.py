from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS, STORAGE_CHANNEL_ID
from database import pdfs

user_step = {}

@Client.on_message(filters.command("addpdf") & filters.user(ADMINS))
async def addpdf(client, message):
    user_step[message.from_user.id] = {
        "step": "exam",
        "last_image": None
    }
    await message.reply(
        "📂 Select Exam",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("SSC", callback_data="exam_SSC")],
            [InlineKeyboardButton("UPSC", callback_data="exam_UPSC")],
            [InlineKeyboardButton("➕ Add New Exam", callback_data="add_exam")]
        ])
    )
@Client.on_callback_query(
    filters.regex("^(exam_|sub_|top_|add_)") & filters.user(ADMINS)
)
async def callback_handler(client, cb):


    

    data = cb.data
    step = user_step[uid]["step"]

    # ---------- ADD NEW FLOW ----------
    if data == "add_exam":
        user_step[uid]["awaiting_input"] = "exam"
        await cb.message.edit("✏️ Send new Exam name")
        return

    if data == "add_subject":
        user_step[uid]["awaiting_input"] = "subject"
        await cb.message.edit("✏️ Send new Subject name")
        return

    if data == "add_topic":
        user_step[uid]["awaiting_input"] = "topic"
        await cb.message.edit("✏️ Send new Topic name")
        return

    # ---------- NORMAL FLOW ----------
    if step == "exam" and data.startswith("exam_"):
        user_step[uid]["exam"] = data.split("_", 1)[1]
        user_step[uid]["step"] = "subject"
        await cb.message.edit(
            "📘 Select Subject",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("History", callback_data="sub_History")],
                [InlineKeyboardButton("Polity", callback_data="sub_Polity")],
                [InlineKeyboardButton("➕ Add New Subject", callback_data="add_subject")]
            ])
        )

    elif step == "subject" and data.startswith("sub_"):
        user_step[uid]["subject"] = data.split("_", 1)[1]
        user_step[uid]["step"] = "topic"
        await cb.message.edit(
            "📗 Select Topic",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Modern", callback_data="top_Modern")],
                [InlineKeyboardButton("Ancient", callback_data="top_Ancient")],
                [InlineKeyboardButton("➕ Add New Topic", callback_data="add_topic")]
            ])
        )

    elif step == "topic" and data.startswith("top_"):
        user_step[uid]["topic"] = data.split("_", 1)[1]
        user_step[uid]["step"] = "upload"
        await cb.message.edit(
            "📤 Send Image (optional) then PDF\nRepeat as needed"
        )

@Client.on_message(filters.photo & filters.user(ADMINS))
async def save_image(client, message):
    uid = message.from_user.id
    if uid not in user_step:
        return
    if user_step[uid].get("step") != "upload":
        return

    # store last image temporarily
    user_step[uid]["last_image"] = message.photo.file_id
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

    # 🧠 attach image if available
    if user_step[uid].get("last_image"):
        data["cover_id"] = user_step[uid]["last_image"]

    await pdfs.insert_one(data)

    # 🔥 clear image after pairing
    user_step[uid]["last_image"] = None

    await message.reply("✅ PDF Stored")

@Client.on_message(filters.text & filters.user(ADMINS))
async def text_input_handler(client, message):
    uid = message.from_user.id
    if uid not in user_step:
        return

    mode = user_step[uid].get("awaiting_input")
    if not mode:
        return

    value = message.text.strip()

    # save new category & auto-select
    user_step[uid][mode] = value
    user_step[uid]["awaiting_input"] = None

    if mode == "exam":
        user_step[uid]["step"] = "subject"
        await message.reply(
            f"✅ Exam added: {value}\n\n📘 Select Subject",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add New Subject", callback_data="add_subject")]
            ])
        )

    elif mode == "subject":
        user_step[uid]["step"] = "topic"
        await message.reply(
            f"✅ Subject added: {value}\n\n📗 Select Topic",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add New Topic", callback_data="add_topic")]
            ])
        )

    elif mode == "topic":
        user_step[uid]["step"] = "upload"
        await message.reply(
            f"✅ Topic added: {value}\n\n📤 Now send Image (optional) then PDF"
        )
