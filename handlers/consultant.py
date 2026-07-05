"""AI-консультант — диалог с Gemini Flash через FSM."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database.db import async_session
from database.models import Product
from ai.consultant import get_ai_response

router = Router()


# Состояние «в диалоге с консультантом»
class ConsultantState(StatesGroup):
    in_chat = State()


@router.callback_query(F.data == "consultant")
async def start_consultant(callback: CallbackQuery, state: FSMContext):
    """Начать диалог с AI-консультантом"""
    await callback.message.answer(
        "💬 <b>AI-консультант</b>\n\n"
        "Задай вопрос о товарах — я помогу с выбором!\n"
        "Напиши <b>/stop</b> чтобы завершить диалог."
    )
    await state.set_state(ConsultantState.in_chat)
    await callback.answer()


@router.message(ConsultantState.in_chat, F.text == "/stop")
async def stop_consultant(message: Message, state: FSMContext):
    """Завершить диалог с консультантом"""
    await state.clear()
    await message.answer(
        "👋 Диалог завершён.\n\n"
        "Напиши /start чтобы вернуться в главное меню."
    )


@router.message(ConsultantState.in_chat, F.text)
async def handle_consultant_message(message: Message, state: FSMContext):
    """Обработка сообщений в режиме консультанта"""
    # Получаем каталог для контекста
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.is_active == True)
        )
        products = result.scalars().all()

    # Формируем контекст для AI
    if products:
        context = "Товары в каталоге:\n"
        for p in products:
            context += f"- {p.name}: {p.price} ₽ — {p.description or 'нет описания'}\n"
    else:
        context = "Каталог пуст."

    # Получаем ответ от AI
    answer = await get_ai_response(message.text, context)

    # Кнопка завершения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Завершить диалог", callback_data="consultant_stop")]
    ])

    await message.answer(answer, reply_markup=keyboard)


@router.callback_query(F.data == "consultant_stop", ConsultantState.in_chat)
async def stop_consultant_btn(callback: CallbackQuery, state: FSMContext):
    """Завершение диалога через кнопку"""
    await state.clear()
    await callback.message.answer("👋 Диалог завершён.")
    await callback.answer()
