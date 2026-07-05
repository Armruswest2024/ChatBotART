"""Корзина — добавление, удаление, просмотр, оплата."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from database.db import async_session
from database.models import Cart, Product, Order

router = Router()


@router.callback_query(F.data.startswith("add_cart_"))
async def add_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину"""
    product_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        # Проверяем есть ли уже в корзине
        result = await session.execute(
            select(Cart).where(
                Cart.user_id == callback.from_user.id,
                Cart.product_id == product_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.quantity += 1
        else:
            item = Cart(user_id=callback.from_user.id, product_id=product_id)
            session.add(item)

        await session.commit()

    await callback.answer("✅ Добавлено в корзину!", show_alert=True)


@router.callback_query(F.data == "my_cart")
async def show_cart(callback: CallbackQuery):
    """Показать корзину"""
    async with async_session() as session:
        result = await session.execute(
            select(Cart).where(Cart.user_id == callback.from_user.id)
        )
        items = result.scalars().all()

        if not items:
            await callback.message.answer("🛒 Корзина пуста.")
            await callback.answer()
            return

        # Получаем товары
        total = 0
        lines = ["<b>🛒 Корзина:</b>\n"]
        buttons = []

        for item in items:
            product = await session.get(Product, item.product_id)
            if not product or not product.is_active:
                continue

            subtotal = product.price * item.quantity
            total += subtotal
            lines.append(f"• <b>{product.name}</b> × {item.quantity} = {subtotal} ₽")

            buttons.append([
                InlineKeyboardButton(
                    text=f"🗑 {product.name}",
                    callback_data=f"del_cart_{item.id}"
                )
            ])

        if total == 0:
            await callback.message.answer("🛒 Корзина пуста.")
            await callback.answer()
            return

        lines.append(f"\n💰 Итого: <b>{total} ₽</b>")

        buttons.append([
            InlineKeyboardButton(text=f"💳 Оплатить {total} ₽", callback_data="pay_cart")
        ])
        buttons.append([
            InlineKeyboardButton(text="← Каталог", callback_data="catalog")
        ])

        await callback.message.answer(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()


@router.callback_query(F.data.startswith("del_cart_"))
async def delete_from_cart(callback: CallbackQuery):
    """Удалить товар из корзины"""
    cart_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        item = await session.get(Cart, cart_id)
        if item and item.user_id == callback.from_user.id:
            await session.delete(item)
            await session.commit()

    await callback.answer("🗑 Удалено из корзины", show_alert=True)

    # Обновляем отображение корзины
    await show_cart(callback)


@router.callback_query(F.data == "pay_cart")
async def pay_cart(callback: CallbackQuery):
    """Оплата всей корзины"""
    async with async_session() as session:
        result = await session.execute(
            select(Cart).where(Cart.user_id == callback.from_user.id)
        )
        items = result.scalars().all()

        if not items:
            await callback.message.answer("🛒 Корзина пуста.")
            await callback.answer()
            return

        # Собираем информацию о товарах
        product_names = []
        total = 0
        for item in items:
            product = await session.get(Product, item.product_id)
            if product and product.is_active:
                product_names.append(f"{product.name} × {item.quantity}")
                total += product.price * item.quantity

        # Создаём один заказ на всю корзину
        order = Order(
            user_id=callback.from_user.id,
            product_id=items[0].product_id,  # Первый товар (для совместимости)
            payment_system="prodamus",
            amount=total,
            status="pending"
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)

        # Сохраняем список товаров в description заказа (временно)
        order.payment_id = f"cart:{','.join(str(i.product_id) for i in items)}"
        await session.commit()

    # Формируем URL для оплаты
    items_text = " + ".join(product_names)
    success_url = f"https://t.me/{callback.bot.username}?start=paid_{order.id}"
    fail_url = f"https://t.me/{callback.bot.username}?start=fail_{order.id}"

    from payments import prodamus, platega
    payment_url = await prodamus.create_payment(
        order_id=order.id,
        amount=total,
        product_name=items_text[:100],  # Prodamus ограничивает длину
        success_url=success_url,
        fail_url=fail_url
    )

    if not payment_url:
        await callback.message.answer("❌ Не удалось создать платёж. Попробуй позже.")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
        [InlineKeyboardButton(text="← Корзина", callback_data="my_cart")],
    ])

    await callback.message.answer(
        f"📦 Заказ #{order.id}\n\n"
        f"Товары: {items_text}\n"
        f"💰 Сумма: {total} ₽\n\n"
        "Нажми кнопку для оплаты 👇",
        reply_markup=keyboard
    )
    await callback.answer()
