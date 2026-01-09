from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import pdfs
from bson import ObjectId

PAGE_SIZE = 10


# ===================== /pdf COMMAND =====================
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
        "📘 **Select Exam**",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="markdown"
    )


# ===================== CALLBACK FLOW =====================
@Client.on_callback_query(filters.regex("^pdf_"))
async def pdf_flow(client, cb):
    await cb.answer()
    parts = cb.data.split("|")

    # ---------- HOME ----------
    if parts[0] == "pdf_home":
        exams = await pdfs.distinct("exam")

        buttons = [
            [InlineKeyboardButton(e, callback_data=f"pdf_e|{e}")]
            for e in exams
        ]

        await cb.message.edit_text(
            "📘 **Select Exam**",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="markdown"
        )

    # ---------- EXAM ----------
    elif parts[0] == "pdf_e":
        exam = parts[1]

        subs = await pdfs.distinct("subject", {"exam": exam})
        if not subs:
            await cb.message.edit_text("❌ No subjects found")
            return

        buttons = [
            [InlineKeyboardButton(s, callback_data=f"pdf_s|{exam}|{s}")]
            for s in subs
        ]

        buttons.append([
            InlineKeyboardButton("🏠 Home", callback_data="pdf_home")
        ])

        await cb.message.edit_text(
            "📗 **Select Subject**",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="markdown"
        )

    # ---------- SUBJECT ----------
    elif parts[0] == "pdf_s":
        exam, subject = parts[1], parts[2]

        topics = await pdfs.distinct(
            "topic", {"exam": exam, "subject": subject}
        )

        if not topics:
            await cb.message.edit_text("❌ No topics found")
            return

        buttons = [
            [InlineKeyboardButton(t, callback_data=f"pdf_t|{exam}|{subject}|{t}|1")]
            for t in topics
        ]

        buttons.append([
            InlineKeyboardButton("⬅ Back", callback_data=f"pdf_e|{exam}"),
            InlineKeyboardButton("🏠 Home", callback_data="pdf_home")
        ])

        await cb.message.edit_text(
            "📙 **Select Topic**",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="markdown"
        )

    # ---------- TOPIC → PDFs (PAGINATION) ----------
    elif parts[0] == "pdf_t":
        exam, subject, topic = parts[1], parts[2], parts[3]
        page = int(parts[4])

        query = {"exam": exam, "subject": subject, "topic": topic}

        total = await pdfs.count_documents(query)
        total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

        skip = (page - 1) * PAGE_SIZE
        files = await pdfs.find(query).skip(skip).limit(PAGE_SIZE).to_list(None)

        if not files:
            await cb.message.edit_text("❌ No PDFs available")
            return

        buttons = []

        # PDF buttons
        for f in files:
            buttons.append([
                InlineKeyboardButton(
                    f"📄 {f['file_name']}",
                    callback_data=f"open|{f['_id']}"
                )
            ])

        # 🔢 Pagination row
        pagination = []

        if page > 1:
            pagination.append(
                InlineKeyboardButton(
                    "⬅ Prev",
                    callback_data=f"pdf_t|{exam}|{subject}|{topic}|{page-1}"
                )
            )

        start = max(1, page - 2)
        end = min(total_pages, page + 2)

        for p in range(start, end + 1):
            pagination.append(
                InlineKeyboardButton(
                    f"• {p} •" if p == page else str(p),
                    callback_data=f"pdf_t|{exam}|{subject}|{topic}|{p}"
                )
            )

        if page < total_pages:
            pagination.append(
                InlineKeyboardButton(
                    "Next ➡",
                    callback_data=f"pdf_t|{exam}|{subject}|{topic}|{page+1}"
                )
            )

        buttons.append(pagination)

        # Back / Home
        buttons.append([
            InlineKeyboardButton("⬅ Back Topic", callback_data=f"pdf_s|{exam}|{subject}"),
            InlineKeyboardButton("🏠 Home", callback_data="pdf_home")
        ])

        await cb.message.edit_text(
            f"📚 **Available PDFs**\nPage {page}/{total_pages}",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="markdown"
        )


# ===================== OPEN PDF =====================
@Client.on_callback_query(filters.regex("^open\\|"))
async def open_pdf(client, cb):
    await cb.answer()
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
