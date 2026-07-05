"""Настройки бота"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Google Gemini Flash
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Prodamus
PRODAMUS_SHOP_ID = os.getenv("PRODAMUS_SHOP_ID")
PRODAMUS_SECRET_KEY = os.getenv("PRODAMUS_SECRET_KEY")
PRODAMUS_URL = os.getenv("PRODAMUS_URL")

# Platega
PLATEGA_MERCHANT_ID = os.getenv("PLATEGA_MERCHANT_ID")
PLATEGA_SECRET_KEY = os.getenv("PLATEGA_SECRET_KEY")
PLATEGA_URL = os.getenv("PLATEGA_URL")

# База данных
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db")

# Админ
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
