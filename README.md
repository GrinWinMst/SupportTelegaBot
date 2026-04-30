# SupportDawn

# Описание проекта
SupportDawn — это Telegram-бот, предназначенный для автоматизации и упрощения взаимодействия с клиентами. Он позволяет обрабатывать обращения пользователей, структурировать коммуникацию и снижать нагрузку на операторов.
Помимо базового функционала общения, бот предоставляет дополнительные инструменты, адаптируемые под нишевые проекты, такие как интеграция с внешними API, ежедневные награды, рассылка и логирование.

# Команда
Кудряшов Степан - Backend-разработчик / DevOps
Фисенко Роман - Frontend-разработчик (Handlers & UI)

# Стек технологий
Язык: Python 3.10+
Библиотека бота: aiogram 3.x
База данных: MySQL / SQLite
Интеграция: RCON (для связи с сервером)
Управление: Bash/Batch скрипты

И# нструкция по запуску бота локально с XAMPP
Запустите Apache и MySQL
Откройте браузер и перейдите на http://localhost/phpmyadmin
Нажмите "Новая" (или "New") слева
Введите имя базы данных, например: thedawn_bot
Кодировка: utf8mb4_general_ci
Нажмите "Создать"

# Установка зависимостей
Активируйте виртуальное окружение (если есть)
.\.venv\Scripts\Activate.ps1
Установите зависимости
pip install -r requirements.txt
#Запустите бота
python bot.py

useCaseDiagram
    actor Player as "Игрок"
    actor Support as "Саппорт"
    actor Admin as "Администратор"

    package "Система SupportDawn" {
        usecase UC1 as "Создать тикет"
        usecase UC2 as "Получить ежедневную награду"
        usecase UC3 as "Ответить на тикет"
        usecase UC4 as "Закрыть тикет"
        usecase UC5 as "Забанить/Разбанить игрока"
        usecase UC6 as "Просмотр логов"
        usecase UC7 as "RCON команды"
    }

    Player --> UC1
    Player --> UC2
    
    Support --> UC3
    Support --> UC4
    
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
