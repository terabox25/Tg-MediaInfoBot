import os

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
TOKEN = os.getenv("TOKEN", "")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "pdf_bot")

STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID", 0))

# ADMINS comma separated IDs → list[int]
ADMIN_ID = list(
    map(int, os.getenv("ADMIN_ID", "").split(","))) if os.getenv("ADMINS") else []
