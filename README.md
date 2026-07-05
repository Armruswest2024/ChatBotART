# Telegram AI-бот для продажи цифровых товаров

## Функции
- Каталог цифровых товаров
- Оплата через Prodamus / Platega
- Автовыдача файлов после оплаты
- AI-консультант (Google Gemini Flash)
- Личный кабинет покупателя

## Стек
- Python 3.11+
- aiogram 3 (Telegram Bot API)
- SQLAlchemy (ORM)
- aiosqlite (SQLite)
- aiohttp (HTTP-запросы)
- Google Generative AI (Gemini Flash)

## Установка
```bash
pip install -r requirements.txt
cp .env.example .env
# Заполнить .env своими данными
python bot.py
```

## Настройка
1. Создать бота через @BotFather
2. Получить API-ключ от Google AI Studio
3. Зарегистрироваться в Prodamus/Platega
4. Заполнить .env файл

## Структура
```
bot.py              # Точка входа
config.py           # Настройки
database/           # Модели и БД
handlers/           # Обработчики команд
payments/           # Интеграция с платёжками
ai/                 # AI-консультант
services/           # Бизнес-логика
```
