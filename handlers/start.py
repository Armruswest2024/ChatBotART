"""Обработчик /start, главное меню и навигация."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from sqlalchemy import select

from database.db import async_session
from database.models import User

router = Router()


def _main_menu_keyboard():
    """Клавиатура главного меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data="my_cart")],
        [InlineKeyboardButton(text="💬 Консультант", callback_data="consultant")],
        [InlineKeyboardButton(text="📦 Мои покупки", callback_data="my_orders")],
    ])


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Приветствие и главное меню"""
    # Сохраняем пользователя в БД
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name,
            )
            session.add(user)
            await session.commit()

    await message.answer(
        f"👋 Привет, {message.from_user.full_name}!\n\n"
        "Я бот для продажи цифровых товаров.\n"
        "Выбери действие:",
        reply_markup=_main_menu_keyboard(),
    )


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    """Возврат в главное меню по кнопке"""
    await callback.message.answer(
        "Выбери действие:",
        reply_markup=_main_menu_keyboard(),
    )
    await callback.answer()
