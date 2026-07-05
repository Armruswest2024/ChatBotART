"""Каталог товаров — просмотр и выбор для покупки."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from database.db import async_session
from database.models import Product

router = Router()


@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    """Показать список товаров"""
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.is_active == True).order_by(Product.id)
        )
        products = result.scalars().all()

    if not products:
        await callback.message.answer("Каталог пока пуст 🛒")
        await callback.answer()
        return

    # Формируем текст
    lines = ["<b>🛍 Каталог товаров</b>\n"]
    for p in products:
        lines.append(f"• <b>{p.name}</b> — {p.price} ₽")
        if p.description:
            lines.append(f"  <i>{p.description}</i>")
        lines.append("")

    # Кнопки товаров
    buttons = []
    for p in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{p.name} — {p.price} ₽",
                callback_data=f"product_{p.id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("\n".join(lines), reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery):
    """Показать карточку товара"""
    product_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        product = await session.get(Product, product_id)

    if not product:
        await callback.message.answer("Товар не найден 😕")
        await callback.answer()
        return

    # Кнопки покупки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Prodamus",
                callback_data=f"buy_prodamus_{product.id}"
            ),
            InlineKeyboardButton(
                text="💳 Platega",
                callback_data=f"buy_platega_{product.id}"
            ),
        ],
        [InlineKeyboardButton(text="← Назад", callback_data="catalog")],
    ])

    text = (
        f"<b>{product.name}</b>\n\n"
        f"{product.description or 'Описание отсутствует'}\n\n"
        f"💰 Цена: <b>{product.price} ₽</b>\n\n"
        "Выбери способ оплаты:"
    )
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()
