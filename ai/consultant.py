"""AI-консультант на базе Google Gemini Flash"""
import asyncio
import logging

from google import genai
from google.api_core import exceptions

import config

logger = logging.getLogger(__name__)

# Инициализация клиента
client = genai.Client(api_key=config.GOOGLE_API_KEY)

# Модель (1.5-flash стабильнее на бесплатном тарифе)
MODEL = "gemini-1.5-flash"

# Системный промпт для консультанта
SYSTEM_PROMPT = """Ты — дружелюбный консультант в магазине цифровых товаров.
Твоя задача — помогать клиентам с вопросами о товарах, давать рекомендации.
Отвечай кратко и по делу. Используй эмодзи для дружелюбия.
Если вопрос не связан с товарами — вежливо направь клиента к каталогу."""


async def get_ai_response(user_message: str, context: str = "") -> str:
    """
    Получить ответ от AI с повторными попытками при лимитах.
    user_message — сообщение пользователя
    context — дополнительный контекст (информация о товарах и т.д.)
    """
    # Формируем промпт
    full_prompt = f"{SYSTEM_PROMPT}\n\n"
    if context:
        full_prompt += f"Контекст (каталог товаров):\n{context}\n\n"
    full_prompt += f"Вопрос клиента: {user_message}"

    # Повторные попытки при 429 (rate limit)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=full_prompt
            )
            return response.text

        except exceptions.TooManyRequests:
            # Лимит запросов — ждём и повторяем
            wait = (attempt + 1) * 5  # 5, 10, 15 секунд
            logger.warning(f"Gemini 429: попытка {attempt+1}/{max_retries}, ожидание {wait}с")
            await asyncio.sleep(wait)

        except exceptions.PermissionDenied:
            logger.error("Gemini: неверный API ключ (403)")
            return "❌ Проблема с API-ключом. Обратись к администратору."

        except Exception as e:
            logger.error(f"Gemini ошибка: {e}")
            return "Извини, сейчас не могу ответить. Попробуй позже 🛍"

    # Все попытки исчерпаны
    logger.error("Gemini: все попытки исчерпаны (429)")
    return "⚠️ Сервис временно перегружен. Попробуй через минуту или выбери товар из каталога 🛍"
