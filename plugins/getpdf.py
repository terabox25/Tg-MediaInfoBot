from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import pdfs
from bson import ObjectId


# ================= /pdf =================
@Client.on_message(filters.command("pdf"))
async def get_pdf(client, message):
    exams = await pdfs.distinct("exam")

    if not exams:
        await message.reply("❌ No PDFs available")
        return

    await message.reply(
        "📘 Select Exam",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(e, callback_data=f"pdf_e_{e}")] for e in exams]
        )
    )


# ================= PDF FLOW =================
@Client.on_callback_query(filters.regex("^pdf_(e|s|t)_"))
async def pdf_flow(client, cb):
    data = cb.data

    # -------- Exam --------
    if data.startswith("pdf_e_"):
        exam = data.replace("pdf_e_", "")
        subs = await pdfs.distinct("subject", {"exam": exam})

        if not subs:
            await cb.message.edit("❌ No subjects found")
            return

        await cb.message.edit(
            "📗 Select Subject",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(s, callback_data=f"pdf_s_{exam}_{s}")] for s in subs]
            )
        )

    # -------- Subject --------
    elif data.startswith("pdf_s_"):
        _, _, exam, sub = data.split("_", 3)
        topics = await pdfs.distinct("topic", {"exam": exam, "subject": sub})

        if not topics:
            await cb.message.edit("❌ No topics found")
            return

        await cb.message.edit(
            "📙 Select Topic",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(t, callback_data=f"pdf_t_{exam}_{sub}_{t}")] for t in topics]
            )
        )

    # -------- Topic --------
    elif data.startswith("pdf_t_"):
        _, _, exam, sub, topic = data.split("_", 4)

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
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )


# ================= OPEN PDF =================
@Client.on_callback_query(filters.regex("^open_"))
async def open_pdf(client, cb):
    pdf_id = cb.data.split("_", 1)[1]
    data = await pdfs.find_one({"_id": ObjectId(pdf_id)})

    if not data:
        await cb.answer("❌ File not found", show_alert=True)
        return

    user_id = cb.from_user.id

    # ✅ Image only if available
    if data.get("cover_id"):
        await client.send_photo(
            user_id,
            data["cover_id"],
            caption=f"📘 {data['file_name']}"
        )

    # ✅ PDF always send
    await client.send_document(
        user_id,
        data["file_id"],
        caption=f"📄 {data['file_name']}"
    )
