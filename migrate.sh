#!/bin/bash
# ============================================
# ChatBotART — миграция базы данных
# Добавляет новые колонки если их нет
# ============================================

DB="/opt/ChatBotART/bot.db"

if [ ! -f "$DB" ]; then
    echo "База не найдена — будет создана при запуске."
    exit 0
fi

echo "Проверяю базу данных..."

# Добавляем колонки если их нет (без ошибок если уже есть)
sqlite3 "$DB" "ALTER TABLE products ADD COLUMN photo_path VARCHAR(500);" 2>/dev/null
sqlite3 "$DB" "ALTER TABLE products ADD COLUMN video_path VARCHAR(500);" 2>/dev/null
sqlite3 "$DB" "ALTER TABLE products ADD COLUMN category_id INTEGER REFERENCES categories(id);" 2>/dev/null

echo "Миграция завершена."
