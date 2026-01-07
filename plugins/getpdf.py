from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import pdfs

@filters.command("pdf")
async def get_pdf(client, message):
    exams = await pdfs.distinct("exam")
    buttons = [[InlineKeyboardButton(e, callback_data=f"e_{e}")] for e in exams]
    await message.reply("Select Exam", reply_markup=InlineKeyboardMarkup(buttons))

@filters.callback_query
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
        files = pdfs.find({"exam": exam, "subject": sub, "topic": topic})
        async for f in files:
            await client.send_document(
                cb.from_user.id,
                f["file_id"],
                caption=f"📘 {f['file_name']}"
            )
