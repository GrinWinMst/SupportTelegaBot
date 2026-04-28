#!/bin/bash

# Скрипт запуска бота на Linux хостинге

# Переход в директорию бота
cd "$(dirname "$0")"

# Активация виртуального окружения
source venv/bin/activate

# Запуск бота
python3 bot.py

