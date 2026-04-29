from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from db_instance import db
from keyboards.admin import (
    get_admin_menu, get_rewards_stats_menu, get_ticket_actions,
    get_back_to_admin
)
from keyboards.main import get_back_to_main
from config import ADMIN_IDS, SUPPORT_STAFF_IDS, TICKET_TYPES
import logging

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in ADMIN_IDS


def is_support_staff(user_id: int) -> bool:
    """Проверка прав персонала поддержки"""
    return user_id in (ADMIN_IDS + SUPPORT_STAFF_IDS)


@router.message(Command("admin"))
async def command_admin(message: Message):
    """Команда /admin - вход в админ панель (только для админов)"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ панели.")
        return
    
    open_tickets = await db.get_open_tickets()
    
    await message.answer(
        f"👨‍💼 <b>Админ панель</b>\n\n"
        f"📬 Открытых обращений: {len(open_tickets)}\n\n"
        f"Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )


@router.callback_query(F.data == "admin_menu")
async def callback_admin_menu(callback: CallbackQuery):
    """Главное меню администратора (только для админов)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к админ панели.", show_alert=True)
        return
    
    await callback.answer()
    open_tickets = await db.get_open_tickets()
    
    await callback.message.edit_text(
        f"👨‍💼 <b>Админ панель</b>\n\n"
        f"📬 Открытых обращений: {len(open_tickets)}\n\n"
        f"Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )


@router.callback_query(F.data == "admin_tickets")
async def callback_admin_tickets(callback: CallbackQuery):
    """Список открытых обращений (для админов и сотрудников)"""
    if not is_support_staff(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    tickets = await db.get_open_tickets()
    
    if not tickets:
        await callback.message.edit_text(
            "📬 <b>Открытые обращения</b>\n\n"
            "Нет открытых обращений.",
            parse_mode="HTML",
            reply_markup=get_back_to_admin()
        )
        return
    
    # Формируем список тикетов
    text = "📬 <b>Открытые обращения:</b>\n\n"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    
    for ticket in tickets[:20]:  # Показываем максимум 20 тикетов
        ticket_type = TICKET_TYPES.get(ticket['ticket_type'], 'Неизвестно')
        text += f"#{ticket['id']} - {ticket_type} (@{ticket['username']})\n"
        buttons.append([
            InlineKeyboardButton(
                text=f"Тикет #{ticket['id']} - {ticket_type}",
                callback_data=f"view_ticket_{ticket['id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data.startswith("view_ticket_"))
async def callback_view_ticket(callback: CallbackQuery):
    """Просмотр конкретного тикета (для админов и сотрудников)"""
    if not is_support_staff(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    ticket_id = int(callback.data.split("_")[2])
    
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await callback.message.edit_text(
            "❌ Тикет не найден.",
            reply_markup=get_back_to_admin()
        )
        return
    
    messages = await db.get_ticket_messages(ticket_id)
    
    ticket_type = TICKET_TYPES.get(ticket['ticket_type'], 'Неизвестно')
    assigned_to = ticket.get('assigned_to')
    
    text = f"""📋 <b>Обращение #{ticket_id}</b>

<b>Тип:</b> {ticket_type}
<b>От:</b> @{ticket['username']} (ID: {ticket['user_id']})
<b>Создано:</b> {ticket['created_at']}
<b>Статус:</b> {ticket['status']}
"""
    
    if assigned_to:
        text += f"<b>Взято в работу:</b> ID {assigned_to}\n"
    
    text += f"\n<b>Данные формы:</b>\n{ticket['form_data']}\n"
    
    if messages:
        text += "\n\n<b>💬 Переписка:</b>\n"
        for msg in messages[-5:]:  # Последние 5 сообщений
            text += f"\n@{msg['username']}: {msg['message'][:100]}"
    
    # Проверяем права на назначение
    is_assigned = assigned_to is not None
    can_assign = callback.from_user.id in ADMIN_IDS or (callback.from_user.id in SUPPORT_STAFF_IDS and not is_assigned)
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_ticket_actions(ticket_id, is_assigned, can_assign, ticket['user_id'])
    )


@router.callback_query(F.data.startswith("close_ticket_"))
async def callback_close_ticket(callback: CallbackQuery):
    """Закрыть тикет"""
    ticket_id = int(callback.data.split("_")[2])
    
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await callback.answer("❌ Тикет не найден.", show_alert=True)
        return
    
    # Проверяем права на закрытие
    is_admin = callback.from_user.id in ADMIN_IDS
    is_assigned = ticket.get('assigned_to') == callback.from_user.id
    is_author = ticket['user_id'] == callback.from_user.id
    assigned_to = ticket.get('assigned_to')
    
    # Может закрыть: админ, тот кто взял обращение, или автор обращения
    if not (is_admin or is_assigned or is_author):
        await callback.answer(
            "❌ Вы не можете закрыть это обращение.\n"
            "Только админы или сотрудник, взявший обращение, могут его закрыть.",
            show_alert=True
        )
        return
    
    # Определяем, кто должен быть записан как closed_by для логов
    if is_author:
        # Если закрывает автор обращения
        if assigned_to:
            # Обращение было взято - записываем в логи к сотруднику, который взял
            closed_by = assigned_to
        else:
            # Обращение не было взято - не записываем в логи (closed_by = None)
            closed_by = None
    else:
        # Если закрывает админ или сотрудник - записываем их ID
        closed_by = callback.from_user.id
    
    await db.close_ticket(ticket_id, closed_by)
    
    # Уведомляем пользователя (если закрывает не он сам)
    if not is_author:
        try:
            from bot import bot
            await bot.send_message(
                ticket['user_id'],
                f"✅ <b>Ваше обращение #{ticket_id} закрыто.</b>\n\n"
                f"Спасибо за обращение! Если у вас возникнут еще вопросы - "
                f"вы можете создать новое обращение.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify user about ticket closure: {e}")
    
    await callback.answer("✅ Тикет закрыт!")
    
    # Возвращаемся к списку тикетов
    await callback_admin_tickets(callback)


@router.callback_query(F.data == "admin_rewards_stats")
async def callback_rewards_stats_menu(callback: CallbackQuery):
    """Меню выбора типа статистики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Только администраторы могут просматривать статистику.", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "📊 <b>Статистика наград</b>\n\n"
        "Выберите тип статистики:",
        parse_mode="HTML",
        reply_markup=get_rewards_stats_menu()
    )


# Обработчики выбора типа статистики
@router.callback_query(F.data == "stats_type_daily")
async def callback_stats_type_daily(callback: CallbackQuery):
    """Выбран тип статистики - ежедневные награды"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Только администраторы могут просматривать статистику.", show_alert=True)
        return
    
    await callback.answer()
    from keyboards.admin import get_daily_rewards_stats_period_menu
    await callback.message.edit_text(
        "📊 <b>Статистика ежедневных наград</b>\n\n"
        "Выберите период:",
        parse_mode="HTML",
        reply_markup=get_daily_rewards_stats_period_menu()
    )


@router.callback_query(F.data == "stats_type_pvp")
async def callback_stats_type_pvp(callback: CallbackQuery):
    """Выбран тип статистики - PvP-киты"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Только администраторы могут просматривать статистику.", show_alert=True)
        return
    
    await callback.answer()
    from keyboards.admin import get_pvp_kit_stats_period_menu
    await callback.message.edit_text(
        "⚔️ <b>Статистика PvP-китов</b>\n\n"
        "Выберите период:",
        parse_mode="HTML",
        reply_markup=get_pvp_kit_stats_period_menu()
    )


# Обработчики статистики ежедневных наград
@router.callback_query(F.data.startswith("stats_daily_"))
async def callback_show_daily_stats(callback: CallbackQuery):
    """Показать статистику ежедневных наград за период"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Только администраторы могут просматривать статистику.", show_alert=True)
        return
    
    await callback.answer("⏳ Загрузка статистики...")
    
    period = callback.data.split("_")[2]
    period_names = {
        "today": ("За сегодня", "today"),
        "week": ("За неделю", "week"),
        "month": ("За месяц", "month"),
        "all": ("За всё время", "all_time")
    }
    
    period_name, db_period = period_names.get(period, ("Неизвестно", "today"))
    
    stats = await db.get_reward_stats(db_period)
    
    text = f"📊 <b>Статистика ежедневных наград - {period_name}</b>\n\n"
    text += f"<b>Всего забрало наград:</b> {stats['total']}\n"
    
    if period in ["month", "all"]:
        text += f"<b>Кол-во игроков, которые забрали все награды (7 уровень):</b> {stats['max_level_count']}\n"
    
    if stats['rewards']:
        text += "\n<b>Список игроков:</b>\n\n"
        
        for reward in stats['rewards'][:50]:  # Показываем максимум 50 записей
            username = reward['username'] or "Unknown"
            nickname = reward['minecraft_nickname']
            level = reward['reward_level']
            text += f"@{username} - {nickname} - Уровень {level}\n"
        
        if len(stats['rewards']) > 50:
            text += f"\n... и еще {len(stats['rewards']) - 50} записей"
    else:
        text += "\nЗа этот период никто не забирал награды."
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_back_to_admin()
    )


# Обработчики статистики PvP-китов
@router.callback_query(F.data.startswith("stats_pvp_"))
async def callback_show_pvp_stats(callback: CallbackQuery):
    """Показать статистику PvP-китов за период"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Только администраторы могут просматривать статистику.", show_alert=True)
        return
    
    await callback.answer("⏳ Загрузка статистики...")
    
    period = callback.data.split("_")[2]
    period_names = {
        "today": ("За сегодня", "today"),
        "week": ("За неделю", "week"),
        "month": ("За месяц", "month"),
        "all": ("За всё время", "all_time")
    }
    
    period_name, db_period = period_names.get(period, ("Неизвестно", "today"))
    
    stats = await db.get_pvp_kit_stats(db_period)
    
    text = f"⚔️ <b>Статистика PvP-китов - {period_name}</b>\n\n"
    text += f"<b>Всего выдано китов:</b> {stats['total']}\n"
    
    if stats['claims']:
        text += "\n<b>Список игроков:</b>\n\n"
        
        for claim in stats['claims'][:50]:  # Показываем максимум 50 записей
            username = claim['username'] or "Unknown"
            nickname = claim['minecraft_nickname']
            text += f"@{username} - {nickname}\n"
        
        if len(stats['claims']) > 50:
            text += f"\n... и еще {len(stats['claims']) - 50} записей"
    else:
        text += "\nЗа этот период никто не получал PvP-киты."
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_back_to_admin()
    )


# Обработчики управления PvP-китами
@router.callback_query(F.data == "admin_pvp_kit")
async def callback_admin_pvp_kit(callback: CallbackQuery):
    """Меню управления PvP-китами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    
    is_enabled = await db.is_pvp_kit_enabled()
    status = "✅ Включено" if is_enabled else "❌ Выключено"
    
    from keyboards.admin import get_pvp_kit_toggle_keyboard
    await callback.message.edit_text(
        f"🎁 <b>Управление бесплатными PvP-китами</b>\n\n"
        f"<b>Текущий статус:</b> {status}\n\n"
        f"При включении пользователи смогут получать бесплатные PvP-наборы каждые 3 часа.",
        parse_mode="HTML",
        reply_markup=get_pvp_kit_toggle_keyboard(is_enabled)
    )


@router.callback_query(F.data == "toggle_pvp_kit_on")
async def callback_toggle_pvp_kit_on(callback: CallbackQuery):
    """Включить функцию PvP-китов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await db.set_pvp_kit_enabled(True, callback.from_user.id)
    await callback.answer("✅ Бесплатные PvP-киты включены!")
    
    from keyboards.admin import get_pvp_kit_toggle_keyboard
    await callback.message.edit_text(
        f"🎁 <b>Управление бесплатными PvP-китами</b>\n\n"
        f"<b>Текущий статус:</b> ✅ Включено\n\n"
        f"При включении пользователи смогут получать бесплатные PvP-наборы каждые 3 часа.",
        parse_mode="HTML",
        reply_markup=get_pvp_kit_toggle_keyboard(True)
    )


@router.callback_query(F.data == "toggle_pvp_kit_off")
async def callback_toggle_pvp_kit_off(callback: CallbackQuery):
    """Выключить функцию PvP-китов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await db.set_pvp_kit_enabled(False, callback.from_user.id)
    await callback.answer("❌ Бесплатные PvP-киты выключены!")
    
    from keyboards.admin import get_pvp_kit_toggle_keyboard
    await callback.message.edit_text(
        f"🎁 <b>Управление бесплатными PvP-китами</b>\n\n"
        f"<b>Текущий статус:</b> ❌ Выключено\n\n"
        f"При включении пользователи смогут получать бесплатные PvP-наборы каждые 3 часа.",
        parse_mode="HTML",
        reply_markup=get_pvp_kit_toggle_keyboard(False)
    )


# Обработчик сброса прогресса (измененный)
@router.callback_query(F.data == "admin_reset_progress")
async def callback_admin_reset_progress(callback: CallbackQuery):
    """Меню выбора типа для сброса прогресса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    from keyboards.admin import get_reset_type_menu
    await callback.message.edit_text(
        "🔄 <b>Сброс прогресса</b>\n\n"
        "Выберите тип:",
        parse_mode="HTML",
        reply_markup=get_reset_type_menu()
    )


# Старый обработчик совместимости (может использоваться в других местах)
@router.callback_query(F.data.startswith("stats_"))
async def callback_show_stats_compat(callback: CallbackQuery):
    """Обработчик для совместимости со старыми callback-датами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Только администраторы могут просматривать статистику.", show_alert=True)
        return
    
    # Этот обработчик теперь не используется, но оставлен для совместимости
    await callback.answer("⚠️ Используйте новое меню статистики")
    await callback_rewards_stats_menu(callback)



# Обработчик для ответа на тикет от администрации
@router.message(F.reply_to_message)
async def handle_admin_reply(message: Message):
    """Обработка ответа администратора на тикет"""
    if not is_support_staff(message.from_user.id):
        return
    
    # Проверяем, является ли это ответом на уведомление о тикете
    replied_text = message.reply_to_message.text
    if not replied_text or "тикете #" not in replied_text.lower():
        return
    
    # Извлекаем ID тикета
    try:
        import re
        match = re.search(r'#(\d+)', replied_text)
        if not match:
            return
        
        ticket_id = int(match.group(1))
        ticket = await db.get_ticket(ticket_id)
        
        if not ticket or ticket['status'] != 'open':
            await message.answer("❌ Тикет не найден или уже закрыт.")
            return
        
        # Сохраняем ответ администратора
        await db.add_ticket_message(ticket_id, message.from_user.id, message.text)
        
        # Отправляем ответ пользователю
        try:
            from bot import bot
            await bot.send_message(
                ticket['user_id'],
                f"💬 <b>Ответ администрации на ваше обращение #{ticket_id}:</b>\n\n"
                f"{message.text}",
                parse_mode="HTML"
            )
            await message.answer("✅ Ваш ответ отправлен пользователю!")
        except Exception as e:
            await message.answer(f"❌ Ошибка при отправке ответа: {e}")
            logger.error(f"Failed to send admin reply to user: {e}")
    
    except Exception as e:
        logger.error(f"Error processing admin reply: {e}")

