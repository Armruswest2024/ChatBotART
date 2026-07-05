"""Обработчик /start и главное меню"""
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from database.db import get_session
from database.models import User

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Приветствие и главное меню"""
    # Сохраняем пользователя в БД
    session = await get_session()
    try:
        user = await session.get(User, message.from_user.id)
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name
            )
            session.add(user)
            await session.commit()
    finally:
        await session.close()

    # Главное меню
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="💬 Консультант", callback_data="consultant")],
        [InlineKeyboardButton(text="📦 Мои покупки", callback_data="my_orders")],
    ])

    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\n\n"
        "Я бот для продажи цифровых товаров.\n"
        "Выбери действие:",
        reply_markup=keyboard
    )
