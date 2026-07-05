"""Обработчик оплаты"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.db import get_session
from database.models import Product, Order, User
from payments import prodamus, platega

router = Router()


@router.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: CallbackQuery):
    """Обработка нажатия кнопки покупки"""
    parts = callback.data.split("_")
    payment_system = parts[1]  # prodamus / platega
    product_id = int(parts[2])

    # Получаем товар
    session = await get_session()
    try:
        product = await session.get(Product, product_id)
        if not product:
            await callback.message.answer("Товар не найден 😕")
            await callback.answer()
            return

        # Создаём заказ
        order = Order(
            user_id=callback.from_user.id,
            product_id=product_id,
            payment_system=payment_system,
            amount=product.price,
            status="pending"
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
    finally:
        await session.close()

    # Формируем URL для оплаты
    success_url = f"https://t.me/{callback.bot.username}?start=paid_{order.id}"
    fail_url = f"https://t.me/{callback.bot.username}?start=fail_{order.id}"

    if payment_system == "prodamus":
        payment_url = await prodamus.create_payment(
            order_id=order.id,
            amount=product.price,
            product_name=product.name,
            success_url=success_url,
            fail_url=fail_url
        )
    elif payment_system == "platega":
        payment_url = await platega.create_payment(
            order_id=order.id,
            amount=product.price,
            product_name=product.name,
            success_url=success_url,
            fail_url=fail_url
        )
    else:
        await callback.message.answer("Неизвестная платёжная система")
        await callback.answer()
        return

    # Кнопка оплаты
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
        [InlineKeyboardButton(text="← Назад", callback_data=f"product_{product_id}")],
    ])

    await callback.message.answer(
        f"📦 Заказ #{order.id}\n\n"
        f"Товар: {product.name}\n"
        f"Сумма: {product.price} ₽\n"
        f"Оплата: {payment_system.title()}\n\n"
        "Нажми кнопку для оплаты 👇",
        reply_markup=keyboard
    )
    await callback.answer()
