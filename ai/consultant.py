"""AI-консультант на базе Groq (Llama 3)"""
import asyncio
import logging

from openai import AsyncOpenAI, RateLimitError, APIError

import config

logger = logging.getLogger(__name__)

# Клиент Groq (совместим с OpenAI API)
client = AsyncOpenAI(
    api_key=config.GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# Модель
MODEL = "llama-3.3-70b-versatile"

# Системный промпт для консультанта
SYSTEM_PROMPT = """Ты — консультант-продажник в магазине цифровых товаров.

Твои правила:
1. Отвечай МАКСИМАЛЬНО кратко — 1-3 предложения. Без воды.
2. Если пользователь хочет купить — скажи «Нажми /catalog и выбери товар»
3. Не повторяй одно и то же. Если уже ответил — не перефразируй.
4. Не используй более 2-3 эмодзи в ответе.
5. Если вопрос не про товары — ответь «Выбери товар в /catalog»
6. Не извиняйся за отсутствие товаров. Просто направь к каталогу.
7. Не спрашивай «Чем могу помочь?» — это уже очевидно."""


async def get_ai_response(user_message: str, context: str = "") -> str:
    """
    Получить ответ от AI с повторными попытками при лимитах.
    user_message — сообщение пользователя
    context — дополнительный контекст (информация о товарах и т.д.)
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    # Добавляем контекст каталога
    if context:
        messages.append({
            "role": "system",
            "content": f"Контекст (каталог товаров):\n{context}"
        })

    messages.append({"role": "user", "content": user_message})

    # Повторные попытки при rate limit
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            return response.choices[0].message.content

        except RateLimitError:
            wait = (attempt + 1) * 5
            logger.warning(f"Groq 429: попытка {attempt+1}/{max_retries}, ожидание {wait}с")
            await asyncio.sleep(wait)

        except APIError as e:
            logger.error(f"Groq API ошибка: {e}")
            return "Извини, сейчас не могу ответить. Попробуй позже 🛍"

        except Exception as e:
            logger.error(f"Groq ошибка: {e}")
            return "Извини, сейчас не могу ответить. Попробуй позже 🛍"

    return "⚠️ Сервис временно перегружен. Попробуй через минуту или выбери товар из каталога 🛍"
