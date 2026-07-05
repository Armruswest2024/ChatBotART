"""Обработчик AI-консультанта"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.db import get_session
from database.models import Product
from ai.consultant import get_ai_response

router = Router()


@router.callback_query(F.data == "consultant")
async def start_consultant(callback: CallbackQuery):
    """Начать диалог с консультантом"""
    await callback.message.answer(
        "💬 Я AI-консультант!\n\n"
        "Задай вопрос о товарах, и я помогу с выбором.\n"
        "Или напиши /catalog чтобы посмотреть каталог."
    )
    await callback.answer()


@router.message(F.text & ~F.text.startswith("/"))
async def handle_message(message: Message):
    """Обработка текстовых сообщений"""
    # Получаем каталог для контекста
    session = await get_session()
    try:
        result = await session.execute(
            Product.__table__.select().where(Product.is_active == True)
        )
        products = result.fetchall()
    finally:
        await session.close()

    # Формируем контекст
    if products:
        context = "Товары в каталоге:\n"
        for p in products:
            context += f"- {p.name}: {p.price} ₽ — {p.description}\n"
    else:
        context = "Каталог пуст."

    # Получаем ответ от AI
    answer = await get_ai_response(message.text, context)

    await message.answer(answer)
