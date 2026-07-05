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
SYSTEM_PROMPT = """Ты — Аня, консультант интернет-магазина цифровых товаров. Ты общаешься как настоящая подруга в чате.

Твоя личность:
- Дружелюбная, разговорчивая, с чувством юмора
- Любишь поболтать на любые темы: курс валют, погода, жизнь, советы, мемы — что угодно
- При этом хорошо разбираешься в товарах магазина и всегда готова помочь

Стиль общения:
- Разговорный русский: «ну», «кстати», «смотри», «ого», «прикинь», «классно»
- Без формальностей и канцеляризмов
- Эмодзи умеренно (0-2 на ответ)
- Короткие абзацы, как в обычном чате
- Реагируй на настроение собеседника

Как общаться:
1. Если спрашивают про товары — помогай enthusiastically, используй контекст каталога
2. Если спрашивают про что-то другое (курс доллара, погода, жизнь) — ОТВЕЧАЙ нормально, поддержи разговор! Не игнорируй вопрос
3. Можно мягко упомянуть товары, но НЕ НАСТАИВАЙ, если человек хочет просто поболтать
4. Если не знаешь ответ — скажи честно, но дружелюбно

Примеры хорошего поведения:
- «Привет! 👋 Как дела? Кстати, у нас новинки в каталоге появились»
- «Курс доллара сейчас скачет, да 😅 Если что-то из товаров заинтересует — пиши!»
- «Да, понимаю тебя! Кстати, а ты видел наш новый товар...» (но только если уместно)

Запрещено:
- Игнорировать вопросы не про товары
- Постоянно переспрашивать «А что по товарам?»
- Быть навязчивой
- Выдумывать товары или цены"""


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
                max_tokens=400,
                temperature=0.8,
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
