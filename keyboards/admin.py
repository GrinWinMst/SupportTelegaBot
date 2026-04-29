from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_menu() -> InlineKeyboardMarkup:
    """Главное меню администратора"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📬 Открытые обращения", callback_data="admin_tickets")],
        [InlineKeyboardButton(text="📊 Статистика наград", callback_data="admin_rewards_stats")],
        [InlineKeyboardButton(text="🎁 Бесплатные киты", callback_data="admin_pvp_kit")],
        [InlineKeyboardButton(text="📋 Логи обращений", callback_data="admin_logs")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📺 Управление каналами", callback_data="admin_channels")],
        [InlineKeyboardButton(text="🚫 Управление банами", callback_data="admin_bans")],
        [InlineKeyboardButton(text="🔄 Сброс прогресса", callback_data="admin_reset_progress")],
        [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="main_menu")]
    ])
    return keyboard


def get_rewards_stats_menu() -> InlineKeyboardMarkup:
    """Меню выбора типа статистики"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Ежедневные награды", callback_data="stats_type_daily")],
        [InlineKeyboardButton(text="⚔️ PvP-киты", callback_data="stats_type_pvp")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")]
    ])
    return keyboard


def get_daily_rewards_stats_period_menu() -> InlineKeyboardMarkup:
    """Меню выбора периода для ежедневных наград"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 За сегодня", callback_data="stats_daily_today")],
        [InlineKeyboardButton(text="📅 За неделю", callback_data="stats_daily_week")],
        [InlineKeyboardButton(text="📅 За месяц", callback_data="stats_daily_month")],
        [InlineKeyboardButton(text="📅 За всё время", callback_data="stats_daily_all")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_rewards_stats")]
    ])
    return keyboard


def get_pvp_kit_stats_period_menu() -> InlineKeyboardMarkup:
    """Меню выбора периода для PvP-китов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 За сегодня", callback_data="stats_pvp_today")],
        [InlineKeyboardButton(text="📅 За неделю", callback_data="stats_pvp_week")],
        [InlineKeyboardButton(text="📅 За месяц", callback_data="stats_pvp_month")],
        [InlineKeyboardButton(text="📅 За всё время", callback_data="stats_pvp_all")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_rewards_stats")]
    ])
    return keyboard


def get_ticket_actions(ticket_id: int, is_assigned: bool = False, can_assign: bool = True, user_id: int = None) -> InlineKeyboardMarkup:
    """Действия с тикетом"""
    buttons = []
    
    if can_assign and not is_assigned:
        buttons.append([InlineKeyboardButton(text="✋ Взять обращение", callback_data=f"assign_ticket_{ticket_id}")])
    elif is_assigned:
        buttons.append([InlineKeyboardButton(text="🔓 Освободить обращение", callback_data=f"unassign_ticket_{ticket_id}")])
    
    buttons.extend([
        [InlineKeyboardButton(text="💬 Написать в чат", callback_data=f"chat_ticket_{ticket_id}")],
        [InlineKeyboardButton(text="🚫 Забанить пользователя", callback_data=f"ban_user_{user_id}_{ticket_id}")],
        [InlineKeyboardButton(text="✅ Закрыть обращение", callback_data=f"close_ticket_{ticket_id}")],
        [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="admin_tickets")]
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_channels_menu() -> InlineKeyboardMarkup:
    """Меню управления каналами"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel")],
        [InlineKeyboardButton(text="📋 Список каналов", callback_data="list_channels")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")]
    ])
    return keyboard


def get_channel_delete_buttons(channels: list) -> InlineKeyboardMarkup:
    """Кнопки для удаления каналов"""
    buttons = []
    for channel in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {channel['channel_name']}", 
                callback_data=f"delete_channel_{channel['channel_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_channels")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_confirm() -> InlineKeyboardMarkup:
    """Подтверждение рассылки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="admin_menu")]
    ])
    return keyboard


def get_back_to_admin() -> InlineKeyboardMarkup:
    """Кнопка возврата в админ меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в админ панель", callback_data="admin_menu")]
    ])
    return keyboard


def get_ban_duration_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора длительности бана"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏱ 3 часа", callback_data="ban_duration_3h")],
        [InlineKeyboardButton(text="📅 1 день", callback_data="ban_duration_1d")],
        [InlineKeyboardButton(text="📅 1 неделя", callback_data="ban_duration_1w")],
        [InlineKeyboardButton(text="♾️ Навсегда", callback_data="ban_duration_permanent")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="admin_menu")]
    ])
    return keyboard


def get_banned_users_keyboard(banned_users: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком забаненных пользователей"""
    buttons = []
    for ban in banned_users:
        user_text = f"User ID: {ban['user_id']} (@{ban['username'] or 'Unknown'})"
        buttons.append([
            InlineKeyboardButton(
                text=f"🔓 {user_text}",
                callback_data=f"unban_{ban['user_id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_logs_menu() -> InlineKeyboardMarkup:
    """Меню логов обращений"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика по сотрудникам", callback_data="logs_staff_stats")],
        [InlineKeyboardButton(text="✅ Закрытые обращения", callback_data="logs_closed_tickets")],
        [InlineKeyboardButton(text="📬 Открытые обращения", callback_data="logs_open_tickets")],
        [InlineKeyboardButton(text="🗑️ Очистить логи", callback_data="logs_cleanup")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")]
    ])
    return keyboard


def get_cleanup_menu() -> InlineKeyboardMarkup:
    """Меню очистки логов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Очистить все логи", callback_data="cleanup_all_confirm")],
        [InlineKeyboardButton(text="👤 Очистить логи сотрудника", callback_data="cleanup_staff")],
        [InlineKeyboardButton(text="✅ Очистить закрытые обращения", callback_data="cleanup_closed_confirm")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_logs")]
    ])
    return keyboard


def get_ticket_list_keyboard(tickets: list, prefix: str = "view_ticket") -> InlineKeyboardMarkup:
    """Клавиатура со списком обращений"""
    buttons = []
    for ticket in tickets[:20]:  # Ограничиваем 20 обращениями
        status_emoji = "✅" if ticket['status'] == 'closed' else "📬"
        ticket_type = ticket['ticket_type'][:20]  # Обрезаем длинные типы
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} #{ticket['id']} - {ticket_type}",
                callback_data=f"{prefix}_{ticket['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="admin_logs")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cleanup_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Подтверждение очистки логов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"cleanup_{action}_yes")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="logs_cleanup")]
    ])
    return keyboard


def get_pvp_kit_toggle_keyboard(is_enabled: bool) -> InlineKeyboardMarkup:
    """Клавиатура управления PvP-китами"""
    if is_enabled:
        button_text = "❌ Выключить"
        callback_data = "toggle_pvp_kit_off"
    else:
        button_text = "✅ Включить"
        callback_data = "toggle_pvp_kit_on"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button_text, callback_data=callback_data)],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")]
    ])
    return keyboard


def get_reset_type_menu() -> InlineKeyboardMarkup:
    """Меню выбора типа для сброса прогресса"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Ежедневные награды", callback_data="reset_type_daily")],
        [InlineKeyboardButton(text="⚔️ PvP-киты", callback_data="reset_type_pvp")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu")]
    ])
    return keyboard
