"""AI-консультант на базе Google Gemini Flash"""
from google import genai

import config

# Инициализация клиента
client = genai.Client(api_key=config.GOOGLE_API_KEY)

# Системный промпт для консультанта
SYSTEM_PROMPT = """Ты — дружелюбный консультант в магазине цифровых товаров.
Твоя задача — помогать клиентам с вопросами о товарах, давать рекомендации.
Отвечай кратко и по делу. Используй эмодзи для дружелюбия.
Если вопрос не связан с товарами — вежливо направь клиента к каталогу."""


async def get_ai_response(user_message: str, context: str = "") -> str:
    """
    Получить ответ от AI
    user_message — сообщение пользователя
    context — дополнительный контекст (информация о товарах и т.д.)
    """
    try:
        # Формируем промпт
        full_prompt = f"{SYSTEM_PROMPT}\n\n"
        if context:
            full_prompt += f"Контекст (каталог товаров):\n{context}\n\n"
        full_prompt += f"Вопрос клиента: {user_message}"

        # Запрос к Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )

        return response.text

    except Exception as e:
        return f"Извини, сейчас не могу ответить. Попробуй позже или выбери товар из каталога 🛍"
