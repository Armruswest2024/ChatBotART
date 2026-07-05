"""Telegram AI-бот для продажи цифровых товаров — точка входа."""
import asyncio
import logging

from aiohttp import web

from core import bot, dp
import config
from database.db import init_db

# Импорт хендлеров (aiogram-роутеры)
from handlers import start, catalog, payment, consultant, admin, my_orders, cart

# Импорт webhook-хендлеров (aiohttp)
from handlers.webhook import register_webhook_routes

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Регистрация aiogram-роутеров
dp.include_router(start.router)
dp.include_router(catalog.router)
dp.include_router(payment.router)
dp.include_router(admin.router)
dp.include_router(my_orders.router)
dp.include_router(cart.router)
dp.include_router(consultant.router)


async def on_startup():
    """Действия при запуске"""
    await init_db()
    logger.info("База данных инициализирована")


async def main():
    """Основная функция — polling + webhook-сервер для оплат"""
    # Регистрация события запуска
    dp.startup.register(on_startup)

    # Создаём aiohttp-приложение для webhook'ов от платёжек
    webhook_app = web.Application()
    register_webhook_routes(webhook_app)

    # Запуск веб-сервера (для Prodamus/Platega webhook'ов)
    runner = web.AppRunner(webhook_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logger.info("Webhook-сервер запущен на порту 8080")
    logger.info("  Prodamus: http://localhost:8080/webhook/prodamus")
    logger.info("  Platega:  http://localhost:8080/webhook/platega")

    # Запуск polling (Telegram-бот)
    logger.info("Бот запущен в режиме polling!")
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
