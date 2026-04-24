import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram import F

from config import BOT_TOKEN
from db_instance import db
from keyboards.main import get_main_menu, get_back_to_main

# Импортируем обработчики
from handlers import daily_rewards, support, admin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


@dp.message(Command("start"))
async def command_start(message: Message):
    """Обработчик команды /start"""
    await db.add_user(message.from_user.id, message.from_user.username)
    
    # Проверяем, включена ли функция PvP-китов
    show_pvp_kit = await db.is_pvp_kit_enabled()
    
    welcome_text = f"""👋 <b>Добро пожаловать на сервер The Dawn Project!</b>

Привет, {message.from_user.first_name}! Я - официальный бот сервера The Dawn Project.

<b>Что я умею:</b>

🎁 <b>Ежедневные награды</b>
Забирай награды каждый день! Чем дольше ты забираешь награды - тем они лучше!
Используй команду <code>!халява ваш_ник</code> или нажми кнопку ниже.

💬 <b>Поддержка</b>
• Подать заявку на медиа (TikTok/YouTube)
• Подать заявку на хелпера
• Задать вопрос по серверу
• Пожаловаться на игрока или администрацию
• Сообщить о баге/дюпе

📜 <b>Правила</b>
Смотрите правила проекта, а главное соблюдайте их!

<b>Начни с кнопок ниже!</b> 👇"""
    
    await message.answer(
        welcome_text,
        parse_mode="HTML",
        reply_markup=get_main_menu(show_pvp_kit=show_pvp_kit)
    )


@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()
    
    # Проверяем, включена ли функция PvP-китов
    show_pvp_kit = await db.is_pvp_kit_enabled()
    
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_main_menu(show_pvp_kit=show_pvp_kit)
    )


@dp.callback_query(F.data == "my_tickets")
async def callback_my_tickets(callback: CallbackQuery):
    """Мои обращения"""
    await callback.answer()
    
    tickets = await db.get_user_tickets(callback.from_user.id)
    
    if not tickets:
        await callback.message.edit_text(
            "📬 <b>Мои обращения</b>\n\n"
            "У вас пока нет обращений.\n"
            "Вы можете создать обращение в разделе 💬 Поддержка",
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from config import TICKET_TYPES
    
    text = f"📬 <b>Ваши обращения ({len(tickets)}):</b>\n\n"
    
    buttons = []
    for ticket in tickets[:10]:  # Показываем максимум 10
        status_emoji = "🟢" if ticket['status'] == 'open' else "⚫"
        ticket_type = TICKET_TYPES.get(ticket['ticket_type'], 'Другое')
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} #{ticket['id']} - {ticket_type}",
                callback_data=f"view_my_ticket_{ticket['id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@dp.callback_query(F.data.startswith("view_my_ticket_"))
async def callback_view_my_ticket(callback: CallbackQuery):
    """Просмотр своего тикета"""
    await callback.answer()
    
    ticket_id = int(callback.data.split("_")[-1])
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket or ticket['user_id'] != callback.from_user.id:
        await callback.message.edit_text(
            "❌ Обращение не найдено.",
            reply_markup=get_back_to_main()
        )
        return
    
    from config import TICKET_TYPES
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    ticket_type = TICKET_TYPES.get(ticket['ticket_type'], 'Неизвестно')
    status = "🟢 Открыто" if ticket['status'] == 'open' else "⚫ Закрыто"
    
    messages = await db.get_ticket_messages(ticket_id)
    
    text = f"""📋 <b>Обращение #{ticket_id}</b>

<b>Тип:</b> {ticket_type}
<b>Статус:</b> {status}
<b>Создано:</b> {ticket['created_at']}

<b>Данные:</b>
{ticket['form_data']}
"""
    
    if messages:
        text += "\n\n<b>💬 История сообщений:</b>\n"
        for msg in messages[-5:]:  # Последние 5 сообщений
            text += f"\n{msg['username']}: {msg['message'][:100]}"
    
    # Используем новую клавиатуру с кнопкой закрытия обращения
    from keyboards.main import get_user_ticket_actions
    
    if ticket['status'] == 'open':
        reply_markup = get_user_ticket_actions(ticket_id)
    else:
        # Если тикет закрыт, показываем только кнопку "Назад"
        buttons = [[InlineKeyboardButton(text="◀️ Назад к списку", callback_data="my_tickets")]]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )


@dp.callback_query(F.data == "info")
async def callback_info(callback: CallbackQuery):
    """Информация о сервере"""
    await callback.answer()
    
    info_text = """ℹ️ <b>Информация о сервере The Dawn Project</b>

<b>🌐 IP адреса:</b>
• play.the-dawn.ru - основной сервер
• ua.the-dawn.fans - если не заходит с основного

<b>📱 Наши ресурсы:</b>
• Сайт: the-dawn.ru
• Telegram: https://t.me/thedawnTG
• ВКонтакте: https://vk.com/thedawnvk
• Discord: https://discord.gg/7bkt6Xm8Dc
• Привязать аккаунт: @thedawntg_bot

<b>🎮 О сервере:</b>
The Dawn Project - это уникальный Minecraft сервер с множеством ивентов и механик!

<b>Используйте бота для:</b>
• Получения ежедневных наград
• Подачи заявок на медиа и хелпера
• Обращения в поддержку"""
    
    await callback.message.edit_text(
        info_text,
        parse_mode="HTML",
        reply_markup=get_back_to_main()
    )


@dp.message(Command("help"))
async def command_help(message: Message):
    """Обработчик команды /help"""
    # Проверяем, включена ли функция PvP-китов
    show_pvp_kit = await db.is_pvp_kit_enabled()
    
    help_text = """📖 <b>Помощь по использованию бота</b>

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать эту справку
/admin - Админ панель (только для админов)

<b>Ежедневные награды:</b>
Используйте команду: <code>!халява ваш_ник</code>
Или нажмите кнопку "🎁 Забрать бесплатную награду"

<b>Система наград:</b>
• День 1: 🗡 железны мечь на остроту 5 + кирка на эфф 5
• День 2: 💨 облегченная руна скорости
• День 3: ❤️ облегченная руна жизни
• День 4: 🎁 кейс с мемными титулами
• День 5: 🟣 Донат CERBERUS на 1 день
• День 6: 👑 набор STINGER
• День 7: 🎁 кейс с аврорами

⚠️ <b>Важно:</b> Если пропустить день - прогресс сбросится!

<b>Поддержка:</b>
Нажмите на кнопку "💬 Поддержка" для:
• Подачи заявок на медиа
• Подачи заявки на хелпера
• Вопросов по серверу
• Жалоб на игроков/администрацию
• Сообщения о багах

Если возникли вопросы - обращайтесь в поддержку!"""
    
    await message.answer(
        help_text,
        parse_mode="HTML",
        reply_markup=get_main_menu(show_pvp_kit=show_pvp_kit)
    )


async def on_startup():
    """Действия при запуске бота"""
    logger.info("Подключение к MySQL...")
    await db.connect()
    logger.info("Инициализация базы данных...")
    await db.init_db()
    logger.info("База данных инициализирована!")
    logger.info("Бот запущен и готов к работе!")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Закрытие подключения к MySQL...")
    await db.close()
    logger.info("Бот остановлен!")


async def main():
    """Главная функция запуска бота"""
    # Импорт новых handlers
    from handlers import chat_system, admin_extended, admin_bans, admin_logs, rules, support_panel, pvp_kit
    
    # Регистрация роутеров
    dp.include_router(daily_rewards.router)
    dp.include_router(pvp_kit.router)
    dp.include_router(support.router)
    dp.include_router(admin.router)
    dp.include_router(support_panel.router)
    dp.include_router(admin_extended.router)
    dp.include_router(admin_bans.router)
    dp.include_router(admin_logs.router)
    dp.include_router(rules.router)
    dp.include_router(chat_system.router)  # Должен быть последним из-за глобального обработчика
    
    # Запуск бота
    await on_startup()
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await on_shutdown()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

