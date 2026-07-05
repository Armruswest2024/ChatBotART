#!/bin/bash
# ============================================
# ChatBotART — обновление
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_DIR="/opt/ChatBotART"

echo -e "${CYAN}Обновление ChatBotART...${NC}"

if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}[ОШИБКА] Бот не найден в $INSTALL_DIR${NC}"
    exit 1
fi

cd "$INSTALL_DIR"

# Обновление кода
echo -e "  → git pull..."
git pull

# Миграция БД
echo -e "  → миграция БД..."
bash migrate.sh

# Обновление зависимостей
echo -e "  → pip install..."
source venv/bin/activate
pip install -q -r requirements.txt

# Перезапуск
echo -e "  → systemctl restart..."
systemctl restart chatbot

sleep 2

if systemctl is-active --quiet chatbot; then
    echo -e "${GREEN}✓ Бот обновлён и перезапущен${NC}"
else
    echo -e "${RED}⚠ Бот не запустился. Логи: journalctl -u chatbot -n 20${NC}"
fi
