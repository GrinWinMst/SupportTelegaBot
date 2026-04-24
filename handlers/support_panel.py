from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from db_instance import db
from keyboards.admin import get_ticket_actions, get_back_to_admin
from keyboards.support import get_support_staff_menu, get_back_to_support
from config import ADMIN_IDS, SUPPORT_STAFF_IDS, TICKET_TYPES
import logging

logger = logging.getLogger(__name__)
router = Router()


def is_support_staff(user_id: int) -> bool:
    """Проверка прав персонала поддержки (без админов)"""
    return user_id in SUPPORT_STAFF_IDS


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in ADMIN_IDS


@router.message(Command("support"))
async def command_support(message: Message):
    """Команда /support - вход в панель поддержки"""
    # Разрешаем доступ как сотрудникам поддержки, так и админам
    if not is_support_staff(message.from_user.id) and not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к панели поддержки.")
        return
    
    open_tickets = await db.get_open_tickets()
    
    await message.answer(
        f"👤 <b>Панель поддержки</b>\n\n"
        f"📬 Открытых обращений: {len(open_tickets)}\n\n"
        f"Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_support_staff_menu()
    )


@router.callback_query(F.data == "support_panel_menu")
async def callback_support_menu(callback: CallbackQuery):
    """Главное меню сотрудника поддержки"""
    # Разрешаем доступ как сотрудникам поддержки, так и админам
    if not is_support_staff(callback.from_user.id) and not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа к панели поддержки.", show_alert=True)
        return
    
    await callback.answer()
    open_tickets = await db.get_open_tickets()
    
    await callback.message.edit_text(
        f"👤 <b>Панель поддержки</b>\n\n"
        f"📬 Открытых обращений: {len(open_tickets)}\n\n"
        f"Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_support_staff_menu()
    )


@router.callback_query(F.data == "support_tickets")
async def callback_support_tickets(callback: CallbackQuery):
    """Список открытых обращений для сотрудника поддержки"""
    # Разрешаем доступ как сотрудникам поддержки, так и админам
    if not is_support_staff(callback.from_user.id) and not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    tickets = await db.get_open_tickets()
    
    if not tickets:
        await callback.message.edit_text(
            "📬 <b>Открытые обращения</b>\n\n"
            "Нет открытых обращений.",
            parse_mode="HTML",
            reply_markup=get_back_to_support()
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
                callback_data=f"support_view_ticket_{ticket['id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="support_panel_menu")])
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data.startswith("support_view_ticket_"))
async def callback_support_view_ticket(callback: CallbackQuery):
    """Просмотр конкретного тикета (для сотрудника поддержки)"""
    # Разрешаем доступ как сотрудникам поддержки, так и админам
    if not is_support_staff(callback.from_user.id) and not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    ticket_id = int(callback.data.split("_")[3])
    
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await callback.message.edit_text(
            "❌ Тикет не найден.",
            reply_markup=get_back_to_support()
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
    
    # Проверяем права на назначение (сотрудник не может взять чужое обращение)
    is_assigned = assigned_to is not None
    can_assign = not is_assigned or assigned_to == callback.from_user.id
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_ticket_actions(ticket_id, is_assigned, can_assign, ticket['user_id'])
    )

