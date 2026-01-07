from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import pdfs
from bson import ObjectId


@Client.on_message(filters.command("pdf"))
async def get_pdf(client, message):
    exams = await pdfs.distinct("exam")

    if not exams:
        await message.reply("❌ No PDFs available")
        return

    buttons = [
        [InlineKeyboardButton(e, callback_data=f"pdf_e|{e}")]
        for e in exams
    ]

    await message.reply(
        "📘 Select Exam",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^pdf_"))
async def pdf_flow(client, cb):
    parts = cb.data.split("|")

    # pdf_e|SSC
    if parts[0] == "pdf_e":
        exam = parts[1]

        subs = await pdfs.distinct("subject", {"exam": exam})
        if not subs:
            await cb.message.edit("❌ No subjects found")
            return

        buttons = [
            [InlineKeyboardButton(s, callback_data=f"pdf_s|{exam}|{s}")]
            for s in subs
        ]

        await cb.message.edit(
            "📗 Select Subject",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # pdf_s|SSC|History
    elif parts[0] == "pdf_s":
        exam, subject = parts[1], parts[2]

        topics = await pdfs.distinct(
            "topic",
            {"exam": exam, "subject": subject}
        )

        if not topics:
            await cb.message.edit("❌ No topics found")
            return

        buttons = [
            [InlineKeyboardButton(t, callback_data=f"pdf_t|{exam}|{subject}|{t}")]
            for t in topics
        ]

        await cb.message.edit(
            "📙 Select Topic",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # pdf_t|SSC|History|Modern
    elif parts[0] == "pdf_t":
        exam, subject, topic = parts[1], parts[2], parts[3]

        files = await pdfs.find({
            "exam": exam,
            "subject": subject,
            "topic": topic
        }).to_list(None)

        if not files:
            await cb.message.edit("❌ No PDFs available")
            return

        buttons = []
        text = "📚 *Available PDFs*\n\n"

        for f in files:
            text += f"• {f['file_name']}\n"
            buttons.append([
                InlineKeyboardButton(
                    f"📄 {f['file_name']}",
                    callback_data=f"open|{f['_id']}"
                )
            ])

        await cb.message.edit(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
@Client.on_callback_query(filters.regex("^open\\|"))
async def open_pdf(client, cb):
    pdf_id = cb.data.split("|")[1]
    data = await pdfs.find_one({"_id": ObjectId(pdf_id)})

    if not data:
        await cb.answer("❌ File not found", show_alert=True)
        return

    uid = cb.from_user.id

    if data.get("cover_id"):
        await client.send_photo(
            uid,
            data["cover_id"],
            caption=f"📘 {data['file_name']}"
        )

    await client.send_document(
        uid,
        data["file_id"],
        caption=f"📄 {data['file_name']}"
    )
