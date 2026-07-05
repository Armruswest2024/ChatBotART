"""Ядро бота — общий экземпляр Bot и Dispatcher.
Вынесен сюда чтобы избежать циклических импортов:
bot.py → handlers → services → bot.py (было).
Теперь: services → core.py, bot.py → core.py (нет цикла).
"""
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

import config

# Экземпляр бота с HTML-разметкой по умолчанию
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

# Диспетчер
dp = Dispatcher()
