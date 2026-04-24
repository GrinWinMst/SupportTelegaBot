from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_main_menu(show_pvp_kit: bool = False) -> InlineKeyboardMarkup:
    """Главное меню бота"""
    buttons = [
        [InlineKeyboardButton(text="🎁 Забрать бесплатную награду", callback_data="daily_reward")]
    ]
    
    # Добавляем кнопку PvP-кита, если функция включена
    if show_pvp_kit:
        buttons.append([InlineKeyboardButton(text="⚔️ Получить PvP-набор", callback_data="pvp_kit")])
    
    buttons.extend([
        [InlineKeyboardButton(text="💬 Поддержка", callback_data="support_menu")],
        [InlineKeyboardButton(text="📬 Мои обращения", callback_data="my_tickets")],
        [InlineKeyboardButton(text="🔗 Привязать аккаунт", url="https://t.me/thedawntg_bot")],
        [InlineKeyboardButton(text="📜 Правила проекта", callback_data="rules")],
        [InlineKeyboardButton(text="ℹ️ Информация о сервере", callback_data="info")]
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_back_to_main() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="main_menu")]
    ])
    return keyboard


def get_back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)]
    ])
    return keyboard


def get_reward_confirmation(callback_data: str) -> InlineKeyboardMarkup:
    """Подтверждение для забора награды"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Забрать награду", callback_data=callback_data)],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    return keyboard


def get_user_ticket_actions(ticket_id: int) -> InlineKeyboardMarkup:
    """Действия пользователя с его обращением"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать в чат", callback_data=f"chat_user_ticket_{ticket_id}")],
        [InlineKeyboardButton(text="✅ Закрыть обращение", callback_data=f"close_ticket_{ticket_id}")],
        [InlineKeyboardButton(text="◀️ Назад к обращениям", callback_data="my_tickets")]
    ])
    return keyboard

