#!/bin/bash
# ============================================
# ChatBotART — просмотр логов
# ============================================

case "$1" in
    follow|f|-f)
        journalctl -u chatbot -f
        ;;
    error|e|-e)
        journalctl -u chatbot -p err -n 50
        ;;
    recent|r|-r)
        journalctl -u chatbot -n 100 --no-pager
        ;;
    *)
        echo "ChatBotART — логи"
        echo ""
        echo "Использование:"
        echo "  bash logs.sh          # последние 100 строк"
        echo "  bash logs.sh follow   # логи в реальном времени"
        echo "  bash logs.sh error    # только ошибки"
        echo "  bash logs.sh recent   # последние 100 строк"
        ;;
esac
