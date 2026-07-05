"""Каталог товаров"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.db import get_session
from database.models import Product

router = Router()


@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    """Показать каталог товаров"""
    session = await get_session()
    try:
        result = await session.execute(
            Product.__table__.select().where(Product.is_active == True)
        )
        products = result.fetchall()
    finally:
        await session.close()

    if not products:
        await callback.message.answer("Каталог пока пуст 🛒")
        await callback.answer()
        return

    # Формируем список товаров
    text = "🛍 **Каталог товаров**\n\n"
    keyboard_buttons = []

    for product in products:
        text += f"**{product.name}** — {product.price} ₽\n"
        text += f"_{product.description}_\n\n"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{product.name} — {product.price} ₽",
                callback_data=f"product_{product.id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery):
    """Показать товар"""
    product_id = int(callback.data.split("_")[1])

    session = await get_session()
    try:
        product = await session.get(Product, product_id)
    finally:
        await session.close()

    if not product:
        await callback.message.answer("Товар не найден 😕")
        await callback.answer()
        return

    # Кнопки покупки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Prodamus", callback_data=f"buy_prodamus_{product.id}"),
            InlineKeyboardButton(text="💳 Platega", callback_data=f"buy_platega_{product.id}"),
        ],
        [InlineKeyboardButton(text="← Назад", callback_data="catalog")],
    ])

    await callback.message.answer(
        f"**{product.name}**\n\n"
        f"{product.description}\n\n"
        f"💰 Цена: **{product.price} ₽**\n\n"
        "Выбери способ оплаты:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()
