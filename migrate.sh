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
sqlite3 "$DB" "ALTER TABLE products ADD COLUMN category_id INTEGER;" 2>/dev/null

# Создаём таблицу cart если её нет
sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);" 2>/dev/null

echo "Миграция завершена."
