from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_support_menu() -> InlineKeyboardMarkup:
    """Главное меню поддержки (для пользователей)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📺 Подать заявку на медиа", callback_data="support_media")],
        [InlineKeyboardButton(text="🛡 Подать заявку на хелпера", callback_data="support_helper")],
        [InlineKeyboardButton(text="❓ Вопрос по серверу", callback_data="support_question")],
        [InlineKeyboardButton(text="⚠️ Жалоба на игрока", callback_data="support_player_complaint")],
        [InlineKeyboardButton(text="🚨 Жалоба на администрацию", callback_data="support_admin_complaint")],
        [InlineKeyboardButton(text="🐛 Нашел баг/дюп", callback_data="support_bug")],
        [InlineKeyboardButton(text="📝 Другое", callback_data="support_other")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])
    return keyboard


def get_media_type_menu() -> InlineKeyboardMarkup:
    """Меню выбора типа медиа"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Я тиктокер", callback_data="media_tiktok")],
        [InlineKeyboardButton(text="🎬 Я ютубер", callback_data="media_youtube")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="support_menu")]
    ])
    return keyboard


def get_form_submit_menu(back_callback: str = "support_menu") -> InlineKeyboardMarkup:
    """Меню подтверждения формы"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="form_submit")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)]
    ])
    return keyboard


def get_after_submit_menu() -> InlineKeyboardMarkup:
    """Меню после отправки заявки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Забрать бесплатную награду", callback_data="daily_reward")],
        [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="main_menu")]
    ])
    return keyboard


def get_cancel_form_button() -> InlineKeyboardMarkup:
    """Кнопка отмены заполнения формы"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="support_menu")]
    ])
    return keyboard


def get_support_staff_menu() -> InlineKeyboardMarkup:
    """Главное меню сотрудника поддержки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📬 Открытые обращения", callback_data="support_tickets")],
        [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="main_menu")]
    ])
    return keyboard


def get_back_to_support() -> InlineKeyboardMarkup:
    """Кнопка возврата в панель поддержки (для сотрудников)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в панель поддержки", callback_data="support_panel_menu")]
    ])
    return keyboard
