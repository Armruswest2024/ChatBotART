# ChatBotART

Telegram-бот для продажи цифровых товаров с AI-консультантом.

## Возможности

- 🛍 **Каталог товаров** — просмотр, выбор, оплата
- 💳 **Оплата** — интеграция с Prodamus и Platega (карты, СБП, QR)
- 📦 **Автовыдача** — файл выдаётся покупателю сразу после оплаты
- 💬 **AI-консультант** — Gemini Flash помогает с выбором товаров
- 📋 **История покупок** — покупатель видит свои заказы
- 🔧 **Админ-панель** — добавление товаров, просмотр заказов и пользователей

## Технологии

| Компонент | Технология |
|-----------|-----------|
| Язык | Python 3.11+ |
| Telegram Bot API | aiogram 3 |
| База данных | SQLAlchemy 2 + SQLite |
| AI | Google Gemini Flash |
| Webhook-сервер | aiohttp |

---

## Установка на VPS

### Быстрая (одна команда)

```bash
git clone https://github.com/Armruswest2024/ChatBotART.git && cd ChatBotART && sudo bash install.sh
```

Скрипт установки:
- Установит Python и зависимости
- Интерактивно спросит токены и ключи
- Настроит автозапуск через systemd
- Бот запустится автоматически

### Вручную

```bash
# 1. Клонировать
git clone https://github.com/Armruswest2024/ChatBotART.git
cd ChatBotART

# 2. Виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 3. Зависимости
pip install -r requirements.txt

# 4. Настройка
cp .env.example .env
nano .env

# 5. Запуск
python bot.py
```

### Автозапуск (systemd)

```bash
cat > /etc/systemd/system/chatbot.service << 'EOF'
[Unit]
Description=ChatBotART Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/ChatBotART
ExecStart=/opt/ChatBotART/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable chatbot
systemctl start chatbot
```

---

## Настройка (.env)

Файл `.env` — параметры запуска. Скопируй из примера и заполни:

```bash
cp .env.example .env
nano .env
```

| Параметр | Где взять | Обязательно |
|----------|-----------|-------------|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) | Да |
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/) | Да |
| `ADMIN_ID` | [@userinfobot](https://t.me/userinfobot) | Да |
| `PRODAMUS_SHOP_ID` | [prodamus.ru](https://prodamus.ru/) | Для оплаты |
| `PRODAMUS_SECRET_KEY` | Prodamus → Настройки | Для оплаты |
| `PRODAMUS_URL` | `https://ваш-домен.payform.ru/` | Для оплаты |
| `PLATEGA_MERCHANT_ID` | [platega.io](https://platega.io/) | Для оплаты |
| `PLATEGA_SECRET_KEY` | Platega → API | Для оплаты |
| `PLATEGA_URL` | `https://app.platega.io` | Для оплаты |

---

## Управление

| Команда | Действие |
|---------|----------|
| `systemctl status chatbot` | Статус бота |
| `systemctl restart chatbot` | Перезапуск |
| `systemctl stop chatbot` | Остановка |
| `journalctl -u chatbot -f` | Логи в реальном времени |
| `bash update.sh` | Обновить бота |
| `bash logs.sh` | Последние 100 строк логов |

---

## Команды в боте

| Команда | Действие |
|---------|----------|
| `/start` | Главное меню |
| `/admin` | Админ-панель (только для ADMIN_ID) |

---

## Структура проекта

```
ChatBotART/
├── bot.py              Точка входа
├── core.py             Экземпляр Bot/Dispatcher
├── config.py           Настройки из .env
├── install.sh          Скрипт установки
├── update.sh           Скрипт обновления
├── logs.sh             Просмотр логов
│
├── database/
│   ├── db.py           Движок БД, фабрика сессий
│   └── models.py       User, Product, Order
│
├── handlers/
│   ├── start.py        /start, главное меню
│   ├── catalog.py      Каталог товаров
│   ├── payment.py      Создание заказа
│   ├── my_orders.py    История покупок
│   ├── consultant.py   AI-консультант (FSM)
│   ├── admin.py        Админ-панель
│   └── webhook.py      Webhook от платёжек
│
├── payments/
│   ├── prodamus.py     Prodamus API
│   └── platega.py      Platega API
│
├── ai/
│   └── consultant.py   Google Gemini Flash
│
├── services/
│   └── delivery.py     Автовыдача файлов
│
├── .env.example        Пример конфига
├── requirements.txt    Зависимости Python
└── README.md           Этот файл
```

---

## Webhook (для оплаты)

Чтобы Prodamus/Platega могли уведомлять об оплате, нужен webhook:

1. Бот слушает на порту **8080**
2. В настройках Prodamus/Platega укажи URL:
   - `http://ВАШ-IP:8080/webhook/prodamus`
   - `http://ВАШ-IP:8080/webhook/platega`

> Без HTTPS оплата работать не будет. Для HTTPS нужен домен + nginx + Let's Encrypt.

---

## FAQ

**Где посмотреть логи?**
```bash
journalctl -u chatbot -f
```

**Как перезапустить бота?**
```bash
systemctl restart chatbot
```

**Как изменить настройки?**
```bash
nano /opt/ChatBotART/.env
systemctl restart chatbot
```

**Бот не запускается, что делать?**
```bash
journalctl -u chatbot -n 50
```
Посмотри ошибки и исправь `.env`.
