import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Minecraft RCON
RCON_HOST = os.getenv("RCON_HOST", "localhost")
RCON_PORT = int(os.getenv("RCON_PORT", 25575))
RCON_PASSWORD = os.getenv("RCON_PASSWORD")

# Admin and Support IDs
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
SUPPORT_STAFF_IDS = [int(id.strip()) for id in os.getenv("SUPPORT_STAFF_IDS", "").split(",") if id.strip()]

# MySQL Database
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "thedawn_bot")

# Daily Rewards Configuration
# Поддержка множественных команд через точку с запятой (;)
# ВАЖНО: Фигурные скобки для NBT-данных Minecraft должны быть экранированы как {{}}
# tellraw используется вместо say для отправки сообщений БЕЗ префикса [Rcon]
DAILY_REWARDS = [
    {"day": 1, "command": "minecraft:give {nickname} iron_sword{{Enchantments:[{{lvl:5,id:sharpness}}]}}; minecraft:give {nickname} minecraft:iron_pickaxe{{Enchantments:[{{lvl:5,id:efficiency}}]}}", "description": "🗡 железный мечь на остроту 5 + кирка на эффективность 5"},
    {"day": 2, "command": "ei give {nickname} ryne_speed_money 1", "description": "💨 облегченная руна скорости"},
    {"day": 3, "command": "ei give {nickname} ryne_hp_money 1", "description": "❤️ облегченная руна жизни"},
    {"day": 4, "command": "dc givekey {nickname} mem 1", "description": "🎁 кейс с мемными титулами"},
    {"day": 5, "command": "lp user {nickname} parent addtemp cerberus 1d", "description": "🟣 Донат CERBERUS на 1 день"},
    {"day": 6, "command": "kit give stinger {nickname}", "description": "👑 набор STINGER"},
    {"day": 7, "command": "dc givekey {nickname} avrora 1", "description": "🎁 кейс с аврорами"},
]

# Support ticket types
TICKET_TYPES = {
    "media_tiktok": "Заявка на медиа (TikTok)",
    "media_youtube": "Заявка на медиа (YouTube)",
    "helper": "Заявка на хелпера",
    "question": "Вопрос по серверу",
    "player_complaint": "Жалоба на игрока",
    "admin_complaint": "Жалоба на администрацию",
    "bug_report": "Нашел баг/дюп",
    "other": "Другое"
}

