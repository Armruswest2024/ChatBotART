"""Обработчик «Мои покупки» — история заказов пользователя."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from database.db import async_session
from database.models import Order, Product

router = Router()

# Статусы на русском
STATUS_TEXT = {
    "pending": "⏳ Ожидает оплаты",
    "paid": "✅ Оплачен",
    "delivered": "📦 Выдан",
}


@router.callback_query(F.data == "my_orders")
async def show_my_orders(callback: CallbackQuery):
    """Показать список покупок пользователя"""
    async with async_session() as session:
        # Получаем заказы пользователя (новые сверху)
        result = await session.execute(
            select(Order)
            .where(Order.user_id == callback.from_user.id)
            .order_by(Order.id.desc())
            .limit(20)
        )
        orders = result.scalars().all()

        # Подтягиваем названия товаров
        product_names = {}
        for order in orders:
            if order.product_id not in product_names:
                product = await session.get(Product, order.product_id)
                product_names[order.product_id] = product.name if product else "Удалён"

    if not orders:
        await callback.message.answer(
            "📦 У тебя пока нет покупок.\n\n"
            "Зайди в каталог, чтобы выбрать товар 🛍"
        )
        await callback.answer()
        return

    # Формируем текст
    lines = ["<b>📦 Мои покупки</b>\n"]
    for o in orders:
        name = product_names.get(o.product_id, "Неизвестно")
        status = STATUS_TEXT.get(o.status, o.status)
        lines.append(f"#{o.id} • {name} — {o.amount} ₽")
        lines.append(f"   {status}")
        lines.append("")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="← Меню", callback_data="main_menu")],
    ])

    await callback.message.answer("\n".join(lines), reply_markup=keyboard)
    await callback.answer()
