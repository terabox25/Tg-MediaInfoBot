import os

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "pdf_bot")

STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID", 0))

# ADMINS comma separated IDs → list[int]
ADMINS = list(
    map(int, os.getenv("ADMINS", "").split(","))) if os.getenv("ADMINS") else []
