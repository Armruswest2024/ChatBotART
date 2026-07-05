"""Telegram AI-бот для продажи цифровых товаров"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

import config
from database.db import init_db
from handlers import start, catalog, payment, consultant, webhook

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Подключение роутеров
dp.include_router(start.router)
dp.include_router(catalog.router)
dp.include_router(payment.router)
dp.include_router(consultant.router)


async def on_startup():
    """Действия при запуске"""
    await init_db()
    logger.info("База данных инициализирована")


async def main():
    """Основная функция"""
    # Регистрация событий
    dp.startup.register(on_startup)

    # Запуск polling
    logger.info("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
