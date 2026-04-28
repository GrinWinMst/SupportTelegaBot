#!/bin/bash

# Скрипт остановки бота

# Переход в директорию бота
cd "$(dirname "$0")"

# Проверка наличия PID файла
if [ ! -f bot.pid ]; then
    echo "❌ Файл bot.pid не найден. Бот не запущен или запущен вручную."
    echo "💡 Попробуйте найти процесс: ps aux | grep bot.py"
    exit 1
fi

# Чтение PID
PID=$(cat bot.pid)

# Проверка, работает ли процесс
if ps -p $PID > /dev/null 2>&1; then
    echo "⛔ Остановка бота (PID: $PID)..."
    kill $PID
    
    # Ждем 5 секунд
    sleep 5
    
    # Проверяем, остановился ли процесс
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️ Процесс не остановился. Принудительная остановка..."
        kill -9 $PID
    fi
    
    rm bot.pid
    echo "✅ Бот остановлен!"
else
    echo "⚠️ Процесс с PID $PID не найден."
    rm bot.pid
fi

