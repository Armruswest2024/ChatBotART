"""Админ-панель — управление товарами, категориями и просмотр заказов."""
import os
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

import config
from database.db import async_session
from database.models import Product, Order, User, Category

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


# ── Состояния FSM ────────────────────────────────────────────

class AddProductFSM(StatesGroup):
    name = State()
    description = State()
    price = State()
    category = State()
    file = State()
    photo = State()
    video = State()


class EditProductFSM(StatesGroup):
    choose_field = State()
    new_value = State()


class AddCategoryFSM(StatesGroup):
    name = State()
    emoji = State()


# ── Главное меню ─────────────────────────────────────────────

@router.message(F.text == "/admin")
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Категории", callback_data="admin_categories")],
        [InlineKeyboardButton(text="📦 Товары", callback_data="admin_products")],
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
    ])
    await message.answer("<b>🔧 Админ-панель</b>", reply_markup=keyboard)


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Категории", callback_data="admin_categories")],
        [InlineKeyboardButton(text="📦 Товары", callback_data="admin_products")],
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
    ])
    await callback.message.answer("<b>🔧 Админ-панель</b>", reply_markup=keyboard)
    await callback.answer()


# ── Категории ────────────────────────────────────────────────

@router.callback_query(F.data == "admin_categories")
async def admin_categories(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(Category).order_by(Category.sort_order))
        categories = result.scalars().all()

    if not categories:
        text = "📂 Категорий пока нет."
    else:
        lines = ["<b>📂 Категории:</b>\n"]
        for c in categories:
            status = "✅" if c.is_active else "❌"
            lines.append(f"{status} #{c.id} {c.emoji or ''} {c.name}")
        text = "\n".join(lines)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_add_category")],
        [InlineKeyboardButton(text="← Назад", callback_data="admin_back")],
    ])
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "admin_add_category")
async def admin_add_category_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    await callback.message.answer("📝 Введи название категории:")
    await state.set_state(AddCategoryFSM.name)
    await callback.answer()


@router.message(AddCategoryFSM.name)
async def admin_add_category_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await message.answer("Теперь эмодзи для категории (или -):")
    await state.set_state(AddCategoryFSM.emoji)


@router.message(AddCategoryFSM.emoji)
async def admin_add_category_emoji(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    emoji = message.text if message.text != "-" else None
    data = await state.get_data()

    async with async_session() as session:
        category = Category(name=data["name"], emoji=emoji)
        session.add(category)
        await session.commit()

    await message.answer(f"✅ Категория «{data['name']}» создана!")
    await state.clear()


# ── Список товаров ───────────────────────────────────────────

@router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(Product).order_by(Product.id)
        )
        products = result.scalars().all()

        # Подтягиваем категории
        cats = {}
        for p in products:
            if p.category_id and p.category_id not in cats:
                cat = await session.get(Category, p.category_id)
                cats[p.category_id] = cat.name if cat else "?"

    if not products:
        await callback.message.answer("Нет товаров.")
        await callback.answer()
        return

    lines = ["<b>📦 Товары:</b>\n"]
    buttons = []
    for p in products:
        status = "✅" if p.is_active else "❌"
        cat = cats.get(p.category_id, "—")
        lines.append(f"{status} #{p.id} <b>{p.name}</b> — {p.price} ₽ [{cat}]")
        buttons.append([
            InlineKeyboardButton(text=f"✏️ #{p.id} {p.name}", callback_data=f"admin_edit_{p.id}"),
            InlineKeyboardButton(text=f"🗑", callback_data=f"admin_del_{p.id}"),
        ])

    buttons.append([InlineKeyboardButton(text="← Назад", callback_data="admin_back")])
    await callback.message.answer("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


# ── Редактирование товара ────────────────────────────────────

@router.callback_query(F.data.startswith("admin_edit_"))
async def admin_edit_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id)

    async with async_session() as session:
        product = await session.get(Product, product_id)

    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data="edit_field_name")],
        [InlineKeyboardButton(text="📖 Описание", callback_data="edit_field_description")],
        [InlineKeyboardButton(text="💰 Цена", callback_data="edit_field_price")],
        [InlineKeyboardButton(text="📂 Категория", callback_data="edit_field_category")],
        [InlineKeyboardButton(text="← Назад", callback_data="admin_products")],
    ])

    await callback.message.answer(
        f"✏️ Редактирование: <b>{product.name}</b>\n\n"
        f"Цена: {product.price} ₽\n"
        f"Категория: {product.category_id or '—'}\n\n"
        "Что изменить?",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field_"))
async def admin_edit_field(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    field = callback.data.replace("edit_field_", "")
    await state.update_data(field=field)

    prompts = {
        "name": "📝 Введи новое название:",
        "description": "📖 Введи новое описание:",
        "price": "💰 Введи новую цену (рубли):",
        "category": "📂 Введи ID категории (или 0 чтобы убрать):",
    }

    await callback.message.answer(prompts.get(field, "Введи новое значение:"))
    await state.set_state(EditProductFSM.new_value)
    await callback.answer()


@router.message(EditProductFSM.new_value)
async def admin_edit_save(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    product_id = data["product_id"]
    field = data["field"]

    async with async_session() as session:
        product = await session.get(Product, product_id)
        if not product:
            await message.answer("Товар не найден")
            await state.clear()
            return

        if field == "price":
            try:
                value = float(message.text.replace(",", ".").replace(" ", ""))
            except ValueError:
                await message.answer("❌ Неверный формат. Введи число:")
                return
            setattr(product, field, value)
        elif field == "category":
            cat_id = int(message.text)
            product.category_id = cat_id if cat_id > 0 else None
        else:
            setattr(product, field, message.text)

        await session.commit()

    await message.answer(f"✅ Поле «{field}» обновлено!")
    await state.clear()


# ── Добавление товара (FSM) ──────────────────────────────────

@router.callback_query(F.data == "admin_add_product")
async def admin_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    await callback.message.answer("📝 <b>Добавление товара</b>\n\nВведи название:")
    await state.set_state(AddProductFSM.name)
    await callback.answer()


@router.message(AddProductFSM.name)
async def admin_add_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(name=message.text)
    await message.answer("Описание товара:")
    await state.set_state(AddProductFSM.description)


@router.message(AddProductFSM.description)
async def admin_add_description(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(description=message.text)
    await message.answer("Цена в рублях (например: 299):")
    await state.set_state(AddProductFSM.price)


@router.message(AddProductFSM.price)
async def admin_add_price(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        price = float(message.text.replace(",", ".").replace(" ", ""))
    except ValueError:
        await message.answer("❌ Неверный формат. Введи число:")
        return

    await state.update_data(price=price)

    # Показываем категории для выбора
    async with async_session() as session:
        result = await session.execute(select(Category).where(Category.is_active == True))
        categories = result.scalars().all()

    if categories:
        lines = ["📂 Выбери категорию (напиши ID) или <b>-</b> для пропуска:\n"]
        buttons = []
        for c in categories:
            lines.append(f"  #{c.id} {c.emoji or ''} {c.name}")
            buttons.append([InlineKeyboardButton(
                text=f"{c.emoji or ''} {c.name}",
                callback_data=f"add_cat_{c.id}"
            )])
        buttons.append([InlineKeyboardButton(text="— Без категории", callback_data="add_cat_0")])
        await message.answer("\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        await state.set_state(AddProductFSM.category)
    else:
        await state.update_data(category_id=None)
        await message.answer("📎 Отправь файл для выдачи (или <b>-</b>):")
        await state.set_state(AddProductFSM.file)


@router.callback_query(F.data.startswith("add_cat_"))
async def admin_add_category_select(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    cat_id = int(callback.data.split("_")[2])
    await state.update_data(category_id=cat_id if cat_id > 0 else None)
    await callback.message.answer("📎 Отправь файл для выдачи (или <b>-</b>):")
    await state.set_state(AddProductFSM.file)
    await callback.answer()


@router.message(AddProductFSM.file)
async def admin_add_file(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    file_path = None

    if message.document:
        files_dir = os.path.join(os.path.dirname(__file__), "..", "files")
        os.makedirs(files_dir, exist_ok=True)
        file_path = os.path.join(files_dir, message.document.file_name)
        await message.bot.download(message.document, file_path)

    await state.update_data(file_path=file_path)
    await message.answer(
        "📸 Отправь фото товара (или <b>-</b> чтобы пропустить):\n\n"
        "Фото будут показаны клиенту при просмотре товара."
    )
    await state.set_state(AddProductFSM.photo)


@router.message(AddProductFSM.photo)
async def admin_add_photo(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    photo_path = None

    if message.photo:
        # Берём фото максимального размера
        photo = message.photo[-1]
        files_dir = os.path.join(os.path.dirname(__file__), "..", "files")
        os.makedirs(files_dir, exist_ok=True)
        photo_path = os.path.join(files_dir, f"photo_{photo.file_id}.jpg")
        try:
            await message.bot.download(photo, photo_path)
        except Exception as e:
            logger.error(f"Ошибка скачивания фото: {e}")
            await message.answer("❌ Не удалось скачать фото. Попробуй другое или пропусти (-).")
            return

    await state.update_data(photo_path=photo_path)
    await message.answer(
        "🎬 Отправь видео товара (или <b>-</b> чтобы пропустить):\n\n"
        "Видео-обзор или демонстрация товара."
    )
    await state.set_state(AddProductFSM.video)


@router.message(AddProductFSM.video)
async def admin_add_video(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    video_path = None

    # Поддерживаем и видео и кружочки (video_note)
    video = message.video or message.video_note
    if video:
        files_dir = os.path.join(os.path.dirname(__file__), "..", "files")
        os.makedirs(files_dir, exist_ok=True)
        ext = "mp4"
        video_path = os.path.join(files_dir, f"video_{video.file_id}.{ext}")
        try:
            await message.bot.download(video, video_path)
        except Exception as e:
            logger.error(f"Ошибка скачивания видео: {e}")
            await message.answer("❌ Не удалось скачать видео. Попробуй меньший файл или пропусти (-).")
            return

    # Создаём товар
    async with async_session() as session:
        product = Product(
            name=data["name"],
            description=data["description"],
            price=data["price"],
            file_path=data.get("file_path"),
            photo_path=data.get("photo_path"),
            video_path=video_path,
            category_id=data.get("category_id"),
            is_active=True,
        )
        session.add(product)
        await session.commit()

    media_info = []
    if data.get("file_path"):
        media_info.append("📁 Файл для выдачи")
    if data.get("photo_path"):
        media_info.append("📸 Фото")
    if video_path:
        media_info.append("🎬 Видео")

    await message.answer(
        f"✅ Товар добавлен!\n\n"
        f"<b>{data['name']}</b>\n"
        f"{data['description']}\n"
        f"💰 {data['price']} ₽\n"
        + ("\n".join(media_info) if media_info else "Без медиа")
    )
    await state.clear()


# ── Удаление товара ──────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_del_"))
async def admin_delete_product(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    product_id = int(callback.data.split("_")[2])
    async with async_session() as session:
        product = await session.get(Product, product_id)
        if product:
            product.is_active = False
            await session.commit()
            await callback.answer(f"#{product_id} деактивирован", show_alert=True)
        else:
            await callback.answer("Не найден", show_alert=True)


# ── Заказы ───────────────────────────────────────────────────

@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(Order).order_by(Order.id.desc()).limit(20))
        orders = result.scalars().all()

        cache = {}
        for o in orders:
            for model, key in [(Product, o.product_id), (User, o.user_id)]:
                if key not in cache:
                    cache[key] = await session.get(model, key)

    if not orders:
        await callback.message.answer("Заказов нет.")
        await callback.answer()
        return

    STATUS = {"pending": "⏳", "paid": "✅", "delivered": "📦"}
    lines = ["<b>📋 Заказы:</b>\n"]
    for o in orders:
        p = cache.get(o.product_id)
        u = cache.get(o.user_id)
        p_name = p.name if p else "?"
        u_name = (u.username or u.full_name) if u else "?"
        lines.append(f"#{o.id} {STATUS.get(o.status, '?')} {p_name} — {o.amount} ₽ | @{u_name}")

    await callback.message.answer("\n".join(lines))
    await callback.answer()


# ── Пользователи ─────────────────────────────────────────────

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.id.desc()))
        users = result.scalars().all()

    lines = [f"<b>👥 Пользователей: {len(users)}</b>\n"]
    for u in users[:30]:
        name = f"@{u.username}" if u.username else u.full_name
        lines.append(f"• {name} (ID: {u.telegram_id})")

    await callback.message.answer("\n".join(lines))
    await callback.answer()
