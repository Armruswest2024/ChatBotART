#!/bin/bash
# ============================================
# ChatBotART — автоматическая установка на VPS
# ============================================

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════╗"
echo "║   ChatBotART — Установка на VPS         ║"
echo "║   Telegram AI-бот для продажи товаров    ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# Проверка root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ОШИБКА] Запусти от root: sudo bash install.sh${NC}"
    exit 1
fi

# Директория установки
INSTALL_DIR="/opt/ChatBotART"
echo -e "${YELLOW}Куда установить?${NC}"
read -p "  [/opt/ChatBotART]: " custom_dir
INSTALL_DIR=${custom_dir:-/opt/ChatBotART}

echo ""
echo -e "${CYAN}━━━ Шаг 1/5: Установка системных пакетов ━━━${NC}"
apt update -qq
apt install -y -qq python3 python3-pip python3-venv git nginx > /dev/null
echo -e "${GREEN}✓ Системные пакеты установлены${NC}"

echo ""
echo -e "${CYAN}━━━ Шаг 2/5: Клонирование репозитория ━━━${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}  Директория уже существует. Обновляю...${NC}"
    cd "$INSTALL_DIR"
    git pull
else
    git clone https://github.com/Armruswest2024/ChatBotART.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi
echo -e "${GREEN}✓ Репозиторий готов${NC}"

echo ""
echo -e "${CYAN}━━━ Шаг 3/5: Создание виртуального окружения ━━━${NC}"
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Зависимости установлены${NC}"

echo ""
echo -e "${CYAN}━━━ Шаг 4/5: Настройка .env ━━━${NC}"

if [ -f ".env" ]; then
    echo -e "${YELLOW}  Файл .env уже существует. Перезаписать? (y/n)${NC}"
    read -p "  [n]: " overwrite
    overwrite=${overwrite:-n}
    if [ "$overwrite" != "y" ]; then
        echo -e "  Пропускаю настройку .env"
    else
        rm .env
    fi
fi

if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}  Введи данные для .env (нажми Enter чтобы пропустить):${NC}"
    echo ""

    read -p "  BOT_TOKEN: " BOT_TOKEN
    read -p "  GOOGLE_API_KEY: " GOOGLE_API_KEY
    read -p "  PRODAMUS_SHOP_ID: " PRODAMUS_SHOP_ID
    read -p "  PRODAMUS_SECRET_KEY: " PRODAMUS_SECRET_KEY
    read -p "  PRODAMUS_URL [https://your-domain.payform.ru/]: " PRODAMUS_URL
    PRODAMUS_URL=${PRODAMUS_URL:-"https://your-domain.payform.ru/"}
    read -p "  PLATEGA_MERCHANT_ID: " PLATEGA_MERCHANT_ID
    read -p "  PLATEGA_SECRET_KEY: " PLATEGA_SECRET_KEY
    read -p "  PLATEGA_URL [https://app.platega.io]: " PLATEGA_URL
    PLATEGA_URL=${PLATEGA_URL:-"https://app.platega.io"}
    read -p "  ADMIN_ID (Telegram ID): " ADMIN_ID

    cat > .env << EOF
# Telegram Bot
BOT_TOKEN=$BOT_TOKEN

# Google Gemini Flash
GOOGLE_API_KEY=$GOOGLE_API_KEY

# Prodamus
PRODAMUS_SHOP_ID=$PRODAMUS_SHOP_ID
PRODAMUS_SECRET_KEY=$PRODAMUS_SECRET_KEY
PRODAMUS_URL=$PRODAMUS_URL

# Platega
PLATEGA_MERCHANT_ID=$PLATEGA_MERCHANT_ID
PLATEGA_SECRET_KEY=$PLATEGA_SECRET_KEY
PLATEGA_URL=$PLATEGA_URL

# База данных
DATABASE_URL=sqlite+aiosqlite:///bot.db

# Админ
ADMIN_ID=$ADMIN_ID
EOF

    echo -e "${GREEN}✓ Файл .env создан${NC}"
fi

echo ""
echo -e "${CYAN}━━━ Шаг 5/5: Настройка systemd-сервиса ━━━${NC}"

cat > /etc/systemd/system/chatbot.service << EOF
[Unit]
Description=ChatBotART Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable chatbot > /dev/null 2>&1
systemctl restart chatbot

sleep 2

if systemctl is-active --quiet chatbot; then
    echo -e "${GREEN}✓ Сервис chatbot запущен${NC}"
else
    echo -e "${RED}⚠ Сервис не запустился. Проверь логи: journalctl -u chatbot -n 20${NC}"
fi

# Открытие порта
if command -v ufw &> /dev/null; then
    ufw allow 8080/tcp > /dev/null 2>&1
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗"
echo "║          Установка завершена!            ║"
echo "╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Бот:      ${CYAN}systemctl status chatbot${NC}"
echo -e "  Логи:     ${CYAN}journalctl -u chatbot -f${NC}"
echo -e "  Рестарт:  ${CYAN}systemctl restart chatbot${NC}"
echo -e "  Стоп:     ${CYAN}systemctl stop chatbot${NC}"
echo -e "  .env:     ${CYAN}nano $INSTALL_DIR/.env${NC}"
echo ""
echo -e "${YELLOW}Webhook URL (настроить в Prodamus/Platega):${NC}"
echo -e "  ${CYAN}http://YOUR-IP:8080/webhook/prodamus${NC}"
echo -e "  ${CYAN}http://YOUR-IP:8080/webhook/platega${NC}"
echo ""
echo -e "${YELLOW}Для HTTPS (рекомендуется для оплаты):${NC}"
echo -e "  Установи nginx + certbot (см. README.md)"
echo ""
