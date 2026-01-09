from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import pdfs
from bson import ObjectId
import re

PAGE_SIZE = 10


# ===================== TEXT SEARCH =====================
@Client.on_message(filters.private & filters.text & ~filters.command([]))
async def search_pdf(client, message):
    query_text = message.text.strip()

    if len(query_text) < 3:
        return

    regex = re.compile(query_text, re.IGNORECASE)

    query = {
        "$or": [
            {"file_name": regex},
            {"exam": regex},
            {"subject": regex},
            {"topic": regex}
        ]
    }

    total = await pdfs.count_documents(query)

    if total == 0:
        await message.reply("❌ No related PDFs found")
        return

    files = await pdfs.find(query).limit(PAGE_SIZE).to_list(None)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    buttons = []
    for f in files:
        buttons.append([
            InlineKeyboardButton(
                f"📄 {f['file_name']}",
                callback_data=f"open|{f['_id']}"
            )
        ])

    if total_pages > 1:
        buttons.append([
            InlineKeyboardButton("Next ➡", callback_data=f"search|{query_text}|2")
        ])

    await message.reply(
        f"🔍 **Search Results for:** `{query_text}`\nPage 1/{total_pages}",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.MARKDOWN
    )


# ===================== SEARCH PAGINATION =====================
@Client.on_callback_query(filters.regex("^search\\|"))
async def search_pagination(client, cb):
    await cb.answer()

    _, query_text, page = cb.data.split("|")
    page = int(page)

    regex = re.compile(query_text, re.IGNORECASE)
    query = {
        "$or": [
            {"file_name": regex},
            {"exam": regex},
            {"subject": regex},
            {"topic": regex}
        ]
    }

    total = await pdfs.count_documents(query)
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE

    skip = (page - 1) * PAGE_SIZE
    files = await pdfs.find(query).skip(skip).limit(PAGE_SIZE).to_list(None)

    if not files:
        await cb.message.edit_text("❌ No results found")
        return

    buttons = []
    for f in files:
        buttons.append([
            InlineKeyboardButton(
                f"📄 {f['file_name']}",
                callback_data=f"open|{f['_id']}"
            )
        ])

    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton("⬅ Prev", callback_data=f"search|{query_text}|{page-1}")
        )
    if page < total_pages:
        nav.append(
            InlineKeyboardButton("Next ➡", callback_data=f"search|{query_text}|{page+1}")
        )

    buttons.append(nav)

    await cb.message.edit_text(
        f"🔍 **Search Results for:** `{query_text}`\nPage {page}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=enums.ParseMode.MARKDOWN
    )
