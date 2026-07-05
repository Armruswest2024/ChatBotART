"""Админ-панель — управление товарами и просмотр заказов."""
import os
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

import config
from database.db import async_session
from database.models import Product, Order, User

logger = logging.getLogger(__name__)
router = Router()

# Состояния для добавления товара
class AddProductFSM(StatesGroup):
    name = State()
    description = State()
    price = State()
    file = State()


def is_admin(user_id: int) -> bool:
    """Проверка — админ ли пользователь"""
    return user_id == config.ADMIN_ID


# ── Главное меню админа ──────────────────────────────────────

@router.message(F.text == "/admin")
async def cmd_admin(message: Message):
    """Показать админ-меню"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Товары", callback_data="admin_products")],
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
    ])
    await message.answer("<b>🔧 Админ-панель</b>", reply_markup=keyboard)


# ── Список товаров ───────────────────────────────────────────

@router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    """Показать список товаров с кнопками удаления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(Product).order_by(Product.id)
        )
        products = result.scalars().all()

    if not products:
        await callback.message.answer("Нет товаров. Добавь первый! ➕")
        await callback.answer()
        return

    lines = ["<b>📦 Товары:</b>\n"]
    buttons = []
    for p in products:
        status = "✅" if p.is_active else "❌"
        lines.append(f"{status} #{p.id} • <b>{p.name}</b> — {p.price} ₽")
        if p.file_path:
            lines.append(f"   📁 {os.path.basename(p.file_path)}")
        lines.append("")
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 Удалить #{p.id} {p.name}",
                callback_data=f"admin_del_{p.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="admin_back")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("\n".join(lines), reply_markup=keyboard)
    await callback.answer()


# ── Удаление товара ──────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_del_"))
async def admin_delete_product(callback: CallbackQuery):
    """Удалить товар (деактивировать)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    product_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        product = await session.get(Product, product_id)
        if product:
            product.is_active = False
            await session.commit()
            await callback.answer(f"Товар #{product_id} деактивирован", show_alert=True)
        else:
            await callback.answer("Товар не найден", show_alert=True)


# ── Добавление товара (FSM) ──────────────────────────────────

@router.callback_query(F.data == "admin_add_product")
async def admin_add_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback.message.answer(
        "📝 <b>Добавление товара</b>\n\n"
        "Введи название товара:"
    )
    await state.set_state(AddProductFSM.name)
    await callback.answer()


@router.message(AddProductFSM.name)
async def admin_add_name(message: Message, state: FSMContext):
    """Получено название"""
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await message.answer("Теперь введи описание товара:")
    await state.set_state(AddProductFSM.description)


@router.message(AddProductFSM.description)
async def admin_add_description(message: Message, state: FSMContext):
    """Получено описание"""
    if not is_admin(message.from_user.id):
        return
    await state.update_data(description=message.text)
    await message.answer("Теперь введи цену в рублях (например: 299):")
    await state.set_state(AddProductFSM.price)


@router.message(AddProductFSM.price)
async def admin_add_price(message: Message, state: FSMContext):
    """Получена цена"""
    if not is_admin(message.from_user.id):
        return

    try:
        price = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.answer("❌ Неверный формат. Введи число (например: 299):")
        return

    await state.update_data(price=price)
    await message.answer(
        "📎 Теперь отправь файл для выдачи покупателю.\n"
        "Или напиши <b>-</b> чтобы пропустить:"
    )
    await state.set_state(AddProductFSM.file)


@router.message(AddProductFSM.file)
async def admin_add_file(message: Message, state: FSMContext):
    """Получен файл (или пропуск)"""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    file_path = None

    # Если файл прикреплён
    if message.document:
        # Создаём папку для файлов
        files_dir = os.path.join(os.path.dirname(__file__), "..", "files")
        os.makedirs(files_dir, exist_ok=True)

        # Сохраняем файл
        file_path = os.path.join(files_dir, message.document.file_name)
        await message.bot.download(message.document, file_path)

    # Создаём товар
    async with async_session() as session:
        product = Product(
            name=data["name"],
            description=data["description"],
            price=data["price"],
            file_path=file_path,
            is_active=True,
        )
        session.add(product)
        await session.commit()

    await message.answer(
        f"✅ Товар добавлен!\n\n"
        f"<b>{data['name']}</b>\n"
        f"{data['description']}\n"
        f"💰 {data['price']} ₽\n"
        f"📁 {'Есть файл' if file_path else 'Без файла'}"
    )
    await state.clear()


# ── Список заказов ───────────────────────────────────────────

@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    """Показать последние заказы"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(Order).order_by(Order.id.desc()).limit(20)
        )
        orders = result.scalars().all()

        # Подтягиваем данные
        cache = {}
        for o in orders:
            for model, key, field in [
                (Product, o.product_id, "product"),
                (User, o.user_id, "user"),
            ]:
                if key not in cache:
                    obj = await session.get(model, key)
                    cache[key] = obj

    if not orders:
        await callback.message.answer("Заказов пока нет.")
        await callback.answer()
        return

    STATUS = {"pending": "⏳", "paid": "✅", "delivered": "📦"}
    lines = ["<b>📋 Последние заказы:</b>\n"]
    for o in orders:
        product = cache.get(o.product_id)
        user = cache.get(o.user_id)
        p_name = product.name if product else "?"
        u_name = user.username or user.full_name if user else "?"
        icon = STATUS.get(o.status, "?")
        lines.append(
            f"#{o.id} {icon} {p_name} — {o.amount} ₽ | @{u_name}"
        )

    await callback.message.answer("\n".join(lines))
    await callback.answer()


# ── Список пользователей ─────────────────────────────────────

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Показать пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.id.desc()))
        users = result.scalars().all()

    if not users:
        await callback.message.answer("Пользователей пока нет.")
        await callback.answer()
        return

    lines = [f"<b>👥 Пользователей: {len(users)}</b>\n"]
    for u in users[:30]:
        name = f"@{u.username}" if u.username else u.full_name
        lines.append(f"• {name} (ID: {u.telegram_id})")

    await callback.message.answer("\n".join(lines))
    await callback.answer()


# ── Кнопка «Назад» ──────────────────────────────────────────

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Вернуться в главное админ-меню"""
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Товары", callback_data="admin_products")],
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
    ])
    await callback.message.answer("<b>🔧 Админ-панель</b>", reply_markup=keyboard)
    await callback.answer()
