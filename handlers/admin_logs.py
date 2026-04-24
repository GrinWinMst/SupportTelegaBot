"""
Обработчики для системы логов обращений
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db_instance import db
from keyboards.admin import (
    get_logs_menu, get_cleanup_menu, get_ticket_list_keyboard,
    get_cleanup_confirm_keyboard, get_back_to_admin
)
from config import ADMIN_IDS
import logging
import json

logger = logging.getLogger(__name__)
router = Router()


class LogsStates(StatesGroup):
    waiting_for_staff_username = State()


def is_admin(user_id: int) -> bool:
    """Проверка прав администратора"""
    return user_id in ADMIN_IDS


# ===== Главное меню логов =====
@router.callback_query(F.data == "admin_logs")
async def callback_admin_logs(callback: CallbackQuery):
    """Меню логов обращений"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "📋 <b>Логи обращений</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_logs_menu()
    )


# ===== Статистика по сотрудникам =====
@router.callback_query(F.data == "logs_staff_stats")
async def callback_logs_staff_stats(callback: CallbackQuery):
    """Показать статистику по сотрудникам"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    
    # Получаем статистику
    stats = await db.get_staff_statistics()
    
    if not stats:
        await callback.message.edit_text(
            "📊 <b>Статистика по сотрудникам</b>\n\n"
            "❌ Нет завершенных обращений.",
            parse_mode="HTML",
            reply_markup=get_logs_menu()
        )
        return
    
    # Подсчитываем общее количество
    total_closed = sum(s['closed_count'] for s in stats)
    
    # Формируем текст
    text = f"📊 <b>Статистика по сотрудникам</b>\n\n"
    text += f"<b>Всего завершенных обращений:</b> {total_closed}\n\n"
    
    for stat in stats:
        staff_id = stat['closed_by']
        count = stat['closed_count']
        
        # Получаем информацию о сотруднике
        user_info = await db.get_user_info(staff_id)
        username = f"@{user_info['username']}" if user_info and user_info['username'] else f"ID: {staff_id}"
        
        text += f"👤 {username} - {count} обращений\n"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_logs_menu()
    )


# ===== Просмотр закрытых обращений =====
@router.callback_query(F.data == "logs_closed_tickets")
async def callback_logs_closed_tickets(callback: CallbackQuery):
    """Показать список закрытых обращений"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    
    tickets = await db.get_closed_tickets(limit=20)
    
    if not tickets:
        await callback.message.edit_text(
            "✅ <b>Закрытые обращения</b>\n\n"
            "❌ Нет закрытых обращений.",
            parse_mode="HTML",
            reply_markup=get_logs_menu()
        )
        return
    
    await callback.message.edit_text(
        f"✅ <b>Закрытые обращения</b>\n\n"
        f"Всего: {len(tickets)} (показаны последние 20)\n\n"
        f"Нажмите на обращение для просмотра диалога:",
        parse_mode="HTML",
        reply_markup=get_ticket_list_keyboard(tickets, prefix="view_closed_ticket")
    )


# ===== Просмотр открытых обращений =====
@router.callback_query(F.data == "logs_open_tickets")
async def callback_logs_open_tickets(callback: CallbackQuery):
    """Показать список открытых обращений"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    
    tickets = await db.get_open_tickets()
    
    if not tickets:
        await callback.message.edit_text(
            "📬 <b>Открытые обращения</b>\n\n"
            "❌ Нет открытых обращений.",
            parse_mode="HTML",
            reply_markup=get_logs_menu()
        )
        return
    
    await callback.message.edit_text(
        f"📬 <b>Открытые обращения</b>\n\n"
        f"Всего: {len(tickets)}\n\n"
        f"Нажмите на обращение для просмотра диалога:",
        parse_mode="HTML",
        reply_markup=get_ticket_list_keyboard(tickets, prefix="view_open_ticket")
    )


# ===== Просмотр диалога закрытого обращения =====
@router.callback_query(F.data.startswith("view_closed_ticket_"))
async def callback_view_closed_ticket(callback: CallbackQuery):
    """Просмотр диалога закрытого обращения"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    
    ticket_id = int(callback.data.split("_")[-1])
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("❌ Обращение не найдено.", show_alert=True)
        return
    
    # Получаем сообщения
    messages = await db.get_ticket_messages(ticket_id)
    
    # Формируем текст
    text = f"✅ <b>Обращение #{ticket_id} (закрыто)</b>\n\n"
    text += f"<b>Тип:</b> {ticket['ticket_type']}\n"
    text += f"<b>Пользователь:</b> @{ticket['username']}\n"
    
    # Парсим данные формы
    try:
        form_data = json.loads(ticket['form_data'])
        text += f"\n<b>Данные заявки:</b>\n"
        for key, value in form_data.items():
            text += f"• <b>{key}:</b> {value[:100]}\n"
    except:
        pass
    
    # Добавляем сообщения
    if messages:
        text += f"\n<b>💬 История сообщений ({len(messages)}):</b>\n\n"
        for msg in messages[:10]:  # Ограничиваем 10 сообщениями
            username = msg.get('username', 'Unknown')
            msg_text = msg['message'][:150]
            text += f"👤 @{username}:\n{msg_text}\n\n"
    
    # Обрезаем если слишком длинный
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (слишком длинное сообщение)"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_logs_menu()
    )


# ===== Просмотр диалога открытого обращения =====
@router.callback_query(F.data.startswith("view_open_ticket_"))
async def callback_view_open_ticket(callback: CallbackQuery):
    """Просмотр диалога открытого обращения"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    
    ticket_id = int(callback.data.split("_")[-1])
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("❌ Обращение не найдено.", show_alert=True)
        return
    
    # Получаем сообщения
    messages = await db.get_ticket_messages(ticket_id)
    
    # Формируем текст
    text = f"📬 <b>Обращение #{ticket_id} (открыто)</b>\n\n"
    text += f"<b>Тип:</b> {ticket['ticket_type']}\n"
    text += f"<b>Пользователь:</b> @{ticket['username']}\n"
    
    # Парсим данные формы
    try:
        form_data = json.loads(ticket['form_data'])
        text += f"\n<b>Данные заявки:</b>\n"
        for key, value in form_data.items():
            text += f"• <b>{key}:</b> {value[:100]}\n"
    except:
        pass
    
    # Добавляем сообщения
    if messages:
        text += f"\n<b>💬 История сообщений ({len(messages)}):</b>\n\n"
        for msg in messages[:10]:  # Ограничиваем 10 сообщениями
            username = msg.get('username', 'Unknown')
            msg_text = msg['message'][:150]
            text += f"👤 @{username}:\n{msg_text}\n\n"
    
    # Обрезаем если слишком длинный
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (слишком длинное сообщение)"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_logs_menu()
    )


# ===== Очистка логов =====
@router.callback_query(F.data == "logs_cleanup")
async def callback_logs_cleanup(callback: CallbackQuery):
    """Меню очистки логов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "🗑️ <b>Очистка логов</b>\n\n"
        "⚠️ <b>Внимание!</b> Удаление логов - необратимая операция.\n\n"
        "Выберите что удалить:",
        parse_mode="HTML",
        reply_markup=get_cleanup_menu()
    )


# Подтверждение очистки всех логов
@router.callback_query(F.data == "cleanup_all_confirm")
async def callback_cleanup_all_confirm(callback: CallbackQuery):
    """Подтверждение очистки всех логов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "⚠️ <b>ВНИМАНИЕ!</b>\n\n"
        "Вы уверены, что хотите удалить <b>ВСЕ ЛОГИ</b>?\n\n"
        "Это удалит:\n"
        "• Все обращения (открытые и закрытые)\n"
        "• Всю историю сообщений\n"
        "• Всю статистику сотрудников\n\n"
        "⚠️ <b>Это действие НЕОБРАТИМО!</b>",
        parse_mode="HTML",
        reply_markup=get_cleanup_confirm_keyboard("all")
    )


@router.callback_query(F.data == "cleanup_all_yes")
async def callback_cleanup_all_yes(callback: CallbackQuery):
    """Выполнить очистку всех логов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer("🗑️ Удаление логов...", show_alert=False)
    
    try:
        await db.delete_all_ticket_logs()
        await callback.message.edit_text(
            "✅ <b>Успешно!</b>\n\n"
            "Все логи были удалены.",
            parse_mode="HTML",
            reply_markup=get_back_to_admin()
        )
    except Exception as e:
        logger.error(f"Failed to delete all logs: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка при удалении логов</b>\n\n{str(e)}",
            parse_mode="HTML",
            reply_markup=get_cleanup_menu()
        )


# Подтверждение очистки закрытых обращений
@router.callback_query(F.data == "cleanup_closed_confirm")
async def callback_cleanup_closed_confirm(callback: CallbackQuery):
    """Подтверждение очистки закрытых обращений"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    
    # Подсчитываем количество
    closed_tickets = await db.get_closed_tickets(limit=999999)
    count = len(closed_tickets)
    
    await callback.message.edit_text(
        f"⚠️ <b>ВНИМАНИЕ!</b>\n\n"
        f"Вы уверены, что хотите удалить <b>все закрытые обращения</b>?\n\n"
        f"Будет удалено: {count} обращений\n\n"
        f"⚠️ <b>Это действие НЕОБРАТИМО!</b>",
        parse_mode="HTML",
        reply_markup=get_cleanup_confirm_keyboard("closed")
    )


@router.callback_query(F.data == "cleanup_closed_yes")
async def callback_cleanup_closed_yes(callback: CallbackQuery):
    """Выполнить очистку закрытых обращений"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer("🗑️ Удаление...", show_alert=False)
    
    try:
        count = await db.delete_closed_tickets()
        await callback.message.edit_text(
            f"✅ <b>Успешно!</b>\n\n"
            f"Удалено {count} закрытых обращений.",
            parse_mode="HTML",
            reply_markup=get_back_to_admin()
        )
    except Exception as e:
        logger.error(f"Failed to delete closed tickets: {e}")
        await callback.message.edit_text(
            f"❌ <b>Ошибка при удалении</b>\n\n{str(e)}",
            parse_mode="HTML",
            reply_markup=get_cleanup_menu()
        )


# Очистка логов сотрудника
@router.callback_query(F.data == "cleanup_staff")
async def callback_cleanup_staff(callback: CallbackQuery, state: FSMContext):
    """Запросить username сотрудника для очистки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    await state.set_state(LogsStates.waiting_for_staff_username)
    
    await callback.message.edit_text(
        "👤 <b>Очистка логов сотрудника</b>\n\n"
        "Отправьте Telegram username сотрудника (без @)\n\n"
        "Например: <code>username</code>\n\n"
        "Для отмены используйте /cancel",
        parse_mode="HTML"
    )


@router.message(LogsStates.waiting_for_staff_username)
async def process_cleanup_staff_username(message: Message, state: FSMContext):
    """Обработка username сотрудника"""
    if message.text.startswith('/cancel'):
        await state.clear()
        await message.answer("❌ Отменено.")
        return
    
    username = message.text.strip().lstrip('@')
    
    # Ищем пользователя по username
    user = await db.get_user_by_telegram_username(username)
    
    if not user:
        await message.answer(
            f"❌ Пользователь @{username} не найден в базе данных.\n\n"
            f"Попробуйте еще раз или /cancel для отмены."
        )
        return
    
    await state.clear()
    
    # Удаляем логи сотрудника
    try:
        count = await db.delete_staff_tickets(user['user_id'])
        await message.answer(
            f"✅ <b>Успешно!</b>\n\n"
            f"Удалено {count} обращений сотрудника @{username}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to delete staff tickets: {e}")
        await message.answer(
            f"❌ <b>Ошибка при удалении</b>\n\n{str(e)}",
            parse_mode="HTML"
        )


