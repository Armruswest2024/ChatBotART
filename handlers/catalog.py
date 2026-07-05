"""Каталог товаров — просмотр по категориям и выбор для покупки."""
import os

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from sqlalchemy import select

from database.db import async_session
from database.models import Product, Category

router = Router()


@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    """Показать категории или все товары"""
    async with async_session() as session:
        # Получаем категории
        result = await session.execute(
            select(Category).where(Category.is_active == True).order_by(Category.sort_order)
        )
        categories = result.scalars().all()

        # Получаем товары без категории
        result = await session.execute(
            select(Product).where(Product.is_active == True, Product.category_id == None)
        )
        uncategorized = result.scalars().all()

    buttons = []

    # Категории
    for c in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"{c.emoji or '📂'} {c.name}",
                callback_data=f"cat_{c.id}"
            )
        ])

    # Товары без категории — показываем сразу
    if uncategorized and not categories:
        text_lines = ["<b>🛍 Каталог</b>\n"]
        for p in uncategorized:
            text_lines.append(f"• <b>{p.name}</b> — {p.price} ₽")
            buttons.append([
                InlineKeyboardButton(
                    text=f"{p.name} — {p.price} ₽",
                    callback_data=f"product_{p.id}"
                )
            ])
        text = "\n".join(text_lines)
    elif not categories:
        await callback.message.answer("Каталог пуст 🛒")
        await callback.answer()
        return
    else:
        text = "<b>🛍 Выбери категорию:</b>"

    if uncategorized and categories:
        buttons.append([
            InlineKeyboardButton(text="📦 Прочие товары", callback_data="cat_0")
        ])

    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("cat_"))
async def show_category(callback: CallbackQuery):
    """Показать товары в категории"""
    cat_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        if cat_id == 0:
            result = await session.execute(
                select(Product).where(Product.is_active == True, Product.category_id == None)
            )
        else:
            result = await session.execute(
                select(Product).where(Product.is_active == True, Product.category_id == cat_id)
            )
        products = result.scalars().all()

        if cat_id > 0:
            cat = await session.get(Category, cat_id)
            cat_name = f"{cat.emoji or ''} {cat.name}" if cat else "Категория"
        else:
            cat_name = "Прочие товары"

    if not products:
        await callback.message.answer(f"{cat_name}\n\nПока пусто 🛒")
        await callback.answer()
        return

    lines = [f"<b>{cat_name}</b>\n"]
    buttons = []
    for p in products:
        lines.append(f"• <b>{p.name}</b> — {p.price} ₽")
        buttons.append([
            InlineKeyboardButton(
                text=f"{p.name} — {p.price} ₽",
                callback_data=f"product_{p.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="← Каталог", callback_data="catalog")])
    await callback.message.answer("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery):
    """Показать карточку товара с фото/видео"""
    product_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        product = await session.get(Product, product_id)

    if not product:
        await callback.message.answer("Товар не найден 😕")
        await callback.answer()
        return

    # Текст описания
    text = (
        f"<b>{product.name}</b>\n\n"
        f"{product.description or 'Описание отсутствует'}\n\n"
        f"💰 Цена: <b>{product.price} ₽</b>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Prodamus", callback_data=f"buy_prodamus_{product.id}"),
            InlineKeyboardButton(text="💳 Platega", callback_data=f"buy_platega_{product.id}"),
        ],
        [InlineKeyboardButton(text="← Назад", callback_data="catalog")],
    ])

    # Отправляем фото если есть
    if product.photo_path and os.path.exists(product.photo_path):
        photo = FSInputFile(product.photo_path)
        await callback.message.answer_photo(photo=photo, caption=text)

    # Отправляем видео если есть
    if product.video_path and os.path.exists(product.video_path):
        video = FSInputFile(product.video_path)
        await callback.message.answer_video(video=video, caption=f"<b>{product.name}</b> — видео обзор")

    # Кнопки покупки — всегда отдельным сообщением
    await callback.message.answer("Выбери способ оплаты:", reply_markup=keyboard)

    await callback.answer()
