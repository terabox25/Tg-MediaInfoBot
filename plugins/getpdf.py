from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import pdfs
from bson import ObjectId

@Client.on_message(filters.command("pdf"))
async def get_pdf(client, message):
    exams = await pdfs.distinct("exam")
    await message.reply(
        "Select Exam",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(e, callback_data=f"e_{e}")] for e in exams]
        )
    )

@Client.on_callback_query(filters.regex("^(e_|s_|t_)"))
async def pdf_flow(client, cb):
    data = cb.data

    if data.startswith("e_"):
        exam = data[2:]
        subs = await pdfs.distinct("subject", {"exam": exam})
        await cb.message.edit(
            "Select Subject",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(s, callback_data=f"s_{exam}_{s}")] for s in subs]
            )
        )

    elif data.startswith("s_"):
        _, exam, sub = data.split("_")
        topics = await pdfs.distinct("topic", {"exam": exam, "subject": sub})
        await cb.message.edit(
            "Select Topic",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(t, callback_data=f"t_{exam}_{sub}_{t}")] for t in topics]
            )
        )

    elif data.startswith("t_"):
        _, exam, sub, topic = data.split("_")

        files = await pdfs.find(
            {"exam": exam, "subject": sub, "topic": topic}
        ).to_list(None)

        if not files:
            await cb.message.edit("❌ No PDFs available")
            return

        text = "📚 *Available PDFs*\n\n"
        buttons = []

        for i, f in enumerate(files, start=1):
            text += f"{i}. {f['file_name']}\n"
            buttons.append([
                InlineKeyboardButton(
                    f"📄 {f['file_name']}",
                    callback_data=f"open_{str(f['_id'])}"
                )
        ])

    await cb.message.edit(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )




@Client.on_callback_query(filters.regex("^open_"))
async def open_pdf(client, cb):
    pdf_id = cb.data.split("_")[1]
    data = await pdfs.find_one({"_id": ObjectId(pdf_id)})

    if not data:
        await cb.answer("File not found", show_alert=True)
        return

    # ✅ 1️⃣ Image ONLY if available
    if data.get("cover_id"):
        await client.send_photo(
            cb.from_user.id,
            data["cover_id"],
            caption=f"📘 {data['file_name']}"
        )

    # ✅ 2️⃣ PDF ALWAYS send
    await client.send_document(
        cb.from_user.id,
        data["file_id"],
        caption=f"📄 {data['file_name']}"
    )
