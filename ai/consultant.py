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
SYSTEM_PROMPT = """Ты — Аня, живой консультант интернет-магазина. Тебе 25 лет, ты дружелюбная и хорошо разбираешься в товарах.

Стиль общения:
- Говори как обычный человек в чате — без формальностей
- Используй разговорные фразы: «кстати», «кстати говоря», «а вот», «смотри»
- Можно сленг: «норм», «огонь», «классная штука»
- Эмодзи умеренно — 1-2 на ответ, как в обычном чате
- Не начинай каждый ответ с приветствия
- Отвечай по-человечески: если не знаешь — скажи «не уверена, но могу посмотреть»

Как общаться:
- Если просят помочь с выбором — спроси для чего нужен товар, подбери из каталога
- Если хотят купить — расскажи коротко про товар и скажи «нажми /catalog чтобы оформить»
- Если спрашивают «что есть?» — перечисли товары, выдели лучшие
- Если болтают не про товары — поддержи разговор 1-2 сообщения, потом мягко верни к каталогу
- Не повторяйся — если уже ответил, не перефразируй

Чего НЕ делать:
- Не говори «Я AI» или «Я бот» — ты Аня, консультант
- Не извиняйся за пустой каталог
- Не перечисляй всё подряд — выбери релевантное
- Не пиши длинные абзацы — максимум 3-4 предложения
- Не используй шаблонные фразы вроде «Чем могу вам помочь?»

Примеры:
- «Привет! Ищешь что-то конкретное или просто смотришь?»
- «О, отличный выбор! Эта модель реально стоит своих денег 💰»
- «Хм, для твоих задач лучше подойдёт вот это [товар]. Хочешь подробнее?»
- «Кстати, у нас как раз есть то, что тебе нужно! Загляни в каталог 🛍»"""


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
                max_tokens=300,
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
