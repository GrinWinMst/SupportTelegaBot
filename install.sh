#!/bin/bash

# Скрипт установки зависимостей на Linux хостинге

echo "🚀 Установка бота SupportDawn..."
echo ""

# Переход в директорию бота
cd "$(dirname "$0")"

# Проверка наличия Python 3.9+
echo "📌 Проверка Python..."
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    echo "✅ Найден Python 3.10"
elif command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
    echo "✅ Найден Python 3.9"
elif command -v python3.8 &> /dev/null; then
    PYTHON_CMD="python3.8"
    echo "✅ Найден Python 3.8"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "✅ Найден Python 3"
else
    echo "❌ Python 3 не найден!"
    echo ""
    echo "💡 Попробуйте установить вручную:"
    echo "   1. python3.10 -m venv venv"
    echo "   2. source venv/bin/activate"
    echo "   3. pip install -r requirements.txt"
    exit 1
fi

# Создание виртуального окружения
echo ""
echo "📦 Создание виртуального окружения..."
$PYTHON_CMD -m venv venv

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Обновление pip
echo ""
echo "⬆️ Обновление pip..."
pip install --upgrade pip

# Установка зависимостей
echo ""
echo "📥 Установка зависимостей..."
pip install -r requirements.txt

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Создайте файл .env с вашими настройками"
echo "2. Запустите бота: bash start_bot.sh"
echo ""

