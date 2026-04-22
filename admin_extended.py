from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db_instance import db
from keyboards.admin import (
    get_admin_menu, get_channels_menu, get_channel_delete_buttons,
    get_broadcast_confirm, get_back_to_admin
)
from config import ADMIN_IDS, SUPPORT_STAFF_IDS
import logging

logger = logging.getLogger(__name__)
router = Router()


class AdminStates(StatesGroup):
    waiting_for_broadcast_text = State()
    waiting_for_channel_id = State()
    waiting_for_channel_name = State()
    waiting_for_channel_url = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def is_support_staff(user_id: int) -> bool:
    return user_id in (ADMIN_IDS + SUPPORT_STAFF_IDS)


# ===== Система рассылки =====
@router.callback_query(F.data == "admin_broadcast")
async def callback_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    """Начать рассылку"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Только администраторы могут делать рассылку.", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "📢 <b>Рассылка сообщений</b>\n\n"
        "Отправьте текст сообщения, которое будет разослано всем пользователям бота.\n\n"
        "Вы можете использовать HTML форматирование.",
        parse_mode="HTML",
        reply_markup=get_back_to_admin()
    )
    await state.set_state(AdminStates.waiting_for_broadcast_text)


@router.message(AdminStates.waiting_for_broadcast_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    """Обработка текста рассылки"""
    await state.update_data(broadcast_text=message.text or message.caption)
    await state.update_data(broadcast_html=message.html_text)
    
    await message.answer(
        f"<b>Предпросмотр рассылки:</b>\n\n{message.html_text}\n\n"
        f"<b>Вы уверены, что хотите разослать этот текст всем пользователям?</b>",
        parse_mode="HTML",
        reply_markup=get_broadcast_confirm()
    )


@router.callback_query(F.data == "broadcast_confirm")
async def callback_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и отправка рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return
    
    await callback.answer("Начинаю рассылку...")
    
    data = await state.get_data()
    broadcast_html = data.get('broadcast_html', '')
    
    if not broadcast_html:
        await callback.message.edit_text(
            "❌ Ошибка: текст рассылки не найден.",
            reply_markup=get_admin_menu()
        )
        await state.clear()
        return
    
    user_ids = await db.get_all_user_ids()
    
    success_count = 0
    failed_count = 0
    
    from bot import bot
    
    await callback.message.edit_text(
        f"📢 <b>Рассылка началась...</b>\n\n"
        f"Всего пользователей: {len(user_ids)}",
        parse_mode="HTML"
    )
    
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, broadcast_html, parse_mode="HTML")
            success_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
    
    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"Успешно отправлено: {success_count}\n"
        f"Не удалось отправить: {failed_count}",
        parse_mode="HTML",
        reply_markup=get_admin_menu()
    )
    
    await state.clear()
    logger.info(f"Broadcast completed by {callback.from_user.id}: {success_count} успешно, {failed_count} ошибок")


# ===== Управление каналами =====
@router.callback_query(F.data == "admin_channels")
async def callback_admin_channels(callback: CallbackQuery):
    """Меню управления каналами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Только администраторы могут управлять каналами.", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "📺 <b>Управление обязательными каналами</b>\n\n"
        "Пользователи должны быть подписаны на эти каналы для получения наград.",
        parse_mode="HTML",
        reply_markup=get_channels_menu()
    )


@router.callback_query(F.data == "add_channel")
async def callback_add_channel(callback: CallbackQuery, state: FSMContext):
    """Добавить канал"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "➕ <b>Добавление канала</b>\n\n"
        "Отправьте ID канала (например: @thedawnTG или -1001234567890)\n\n"
        "Чтобы получить ID канала:\n"
        "1. Добавьте бота @userinfobot в канал\n"
        "2. Перешлите любое сообщение из канала боту\n"
        "3. Скопируйте 'Forwarded from chat'",
        parse_mode="HTML",
        reply_markup=get_back_to_admin()
    )
    await state.set_state(AdminStates.waiting_for_channel_id)


@router.message(AdminStates.waiting_for_channel_id)
async def process_channel_id(message: Message, state: FSMContext):
    """Обработка ID канала"""
    channel_id = message.text.strip()
    await state.update_data(channel_id=channel_id)
    
    await message.answer(
        "Отлично! Теперь отправьте название канала (как оно будет отображаться пользователям):",
        reply_markup=get_back_to_admin()
    )
    await state.set_state(AdminStates.waiting_for_channel_name)


@router.message(AdminStates.waiting_for_channel_name)
async def process_channel_name(message: Message, state: FSMContext):
    """Обработка названия канала"""
    channel_name = message.text.strip()
    await state.update_data(channel_name=channel_name)
    
    await message.answer(
        "Последний шаг! Отправьте ссылку на канал (например: https://t.me/thedawnTG):",
        reply_markup=get_back_to_admin()
    )
    await state.set_state(AdminStates.waiting_for_channel_url)


@router.message(AdminStates.waiting_for_channel_url)
async def process_channel_url(message: Message, state: FSMContext):
    """Обработка URL канала и сохранение"""
    channel_url = message.text.strip()
    data = await state.get_data()
    
    channel_id = data.get('channel_id')
    channel_name = data.get('channel_name')
    
    try:
        await db.add_required_channel(channel_id, channel_name, channel_url, message.from_user.id)
        
        await message.answer(
            f"✅ <b>Канал добавлен!</b>\n\n"
            f"<b>ID:</b> {channel_id}\n"
            f"<b>Название:</b> {channel_name}\n"
            f"<b>Ссылка:</b> {channel_url}\n\n"
            f"Теперь пользователи должны быть подписаны на этот канал для получения наград.",
            parse_mode="HTML",
            reply_markup=get_admin_menu()
        )
        logger.info(f"Channel added by {message.from_user.id}: {channel_id} - {channel_name}")
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при добавлении канала: {e}",
            reply_markup=get_admin_menu()
        )
        logger.error(f"Failed to add channel: {e}")
    
    await state.clear()


@router.callback_query(F.data == "list_channels")
async def callback_list_channels(callback: CallbackQuery):
    """Список каналов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    
    channels = await db.get_required_channels()
    
    if not channels:
        await callback.message.edit_text(
            "📋 <b>Обязательные каналы</b>\n\n"
            "Пока нет добавленных каналов.\n"
            "Используйте кнопку ➕ Добавить канал.",
            parse_mode="HTML",
            reply_markup=get_channels_menu()
        )
        return
    
    text = "📋 <b>Обязательные каналы:</b>\n\n"
    for channel in channels:
        text += f"• <b>{channel['channel_name']}</b>\n"
        text += f"  ID: <code>{channel['channel_id']}</code>\n"
        text += f"  Ссылка: {channel['channel_url']}\n\n"
    
    text += "Нажмите на канал ниже, чтобы удалить его:"
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_channel_delete_buttons(channels)
    )


@router.callback_query(F.data.startswith("delete_channel_"))
async def callback_delete_channel(callback: CallbackQuery):
    """Удалить канал"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return
    
    channel_id = callback.data.replace("delete_channel_", "")
    
    try:
        await db.remove_required_channel(channel_id)
        await callback.answer("✅ Канал удален!")
        logger.info(f"Channel deleted by {callback.from_user.id}: {channel_id}")
        
        # Обновляем список
        await callback_list_channels(callback)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)
        logger.error(f"Failed to delete channel: {e}")


# ===== Система назначения тикетов =====
@router.callback_query(F.data.startswith("assign_ticket_"))
async def callback_assign_ticket(callback: CallbackQuery):
    """Взять обращение в работу"""
    if not is_support_staff(callback.from_user.id):
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return
    
    ticket_id = int(callback.data.split("_")[2])
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.answer("❌ Тикет не найден.", show_alert=True)
        return
    
    # Проверка: если тикет уже назначен и пользователь не админ
    if ticket.get('assigned_to') and callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Это обращение уже взял другой сотрудник.", show_alert=True)
        return
    
    await db.assign_ticket(ticket_id, callback.from_user.id)
    await callback.answer("✅ Вы взяли обращение в работу!")
    
    # Обновляем сообщение
    from handlers.admin import callback_view_ticket
    await callback_view_ticket(callback)


@router.callback_query(F.data.startswith("unassign_ticket_"))
async def callback_unassign_ticket(callback: CallbackQuery):
    """Освободить обращение"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Только администраторы могут освобождать обращения.", show_alert=True)
        return
    
    ticket_id = int(callback.data.split("_")[2])
    
    await db.unassign_ticket(ticket_id)
    await callback.answer("✅ Обращение освобождено!")
    
    # Обновляем сообщение
    from handlers.admin import callback_view_ticket
    await callback_view_ticket(callback)


# ===== Система сброса прогресса =====
class ResetStates(StatesGroup):
    waiting_for_daily_username = State()
    waiting_for_pvp_username = State()


@router.callback_query(F.data == "reset_type_daily")
async def callback_reset_type_daily(callback: CallbackQuery, state: FSMContext):
    """Выбран сброс ежедневных наград"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "🔄 <b>Сброс задержки ежедневных наград</b>\n\n"
        "Отправьте <b>Telegram username</b> пользователя (без @):",
        parse_mode="HTML",
        reply_markup=get_back_to_admin()
    )
    await state.set_state(ResetStates.waiting_for_daily_username)


@router.callback_query(F.data == "reset_type_pvp")
async def callback_reset_type_pvp(callback: CallbackQuery, state: FSMContext):
    """Выбран сброс PvP-китов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    await callback.message.edit_text(
        "🔄 <b>Сброс задержки PvP-китов</b>\n\n"
        "Отправьте <b>Telegram username</b> пользователя (без @):",
        parse_mode="HTML",
        reply_markup=get_back_to_admin()
    )
    await state.set_state(ResetStates.waiting_for_pvp_username)


@router.message(ResetStates.waiting_for_daily_username)
async def process_reset_daily_username(message: Message, state: FSMContext):
    """Обработка сброса ежедневных наград"""
    username = message.text.strip().lstrip('@')
    
    user = await db.get_user_by_telegram_username(username)
    
    if not user:
        await message.answer(
            f"❌ Пользователь @{username} не найден в базе данных.",
            reply_markup=get_admin_menu()
        )
        await state.clear()
        return
    
    success = await db.reset_reward_cooldown(user['user_id'])
    
    if success:
        await message.answer(
            f"✅ <b>Задержка ежедневных наград сброшена!</b>\n\n"
            f"Пользователь: @{username}\n"
            f"ID: {user['user_id']}\n\n"
            f"Теперь пользователь может забрать награду сразу.",
            parse_mode="HTML",
            reply_markup=get_admin_menu()
        )
        logger.info(f"Daily reward cooldown reset for user {user['user_id']} by admin {message.from_user.id}")
    else:
        await message.answer(
            f"❌ У пользователя @{username} нет прогресса наград для сброса.",
            reply_markup=get_admin_menu()
        )
    
    await state.clear()


@router.message(ResetStates.waiting_for_pvp_username)
async def process_reset_pvp_username(message: Message, state: FSMContext):
    """Обработка сброса PvP-китов"""
    username = message.text.strip().lstrip('@')
    
    user = await db.get_user_by_telegram_username(username)
    
    if not user:
        await message.answer(
            f"❌ Пользователь @{username} не найден в базе данных.",
            reply_markup=get_admin_menu()
        )
        await state.clear()
        return
    
    success = await db.reset_pvp_kit_cooldown(user['user_id'])
    
    if success:
        await message.answer(
            f"✅ <b>Задержка PvP-китов сброшена!</b>\n\n"
            f"Пользователь: @{username}\n"
            f"ID: {user['user_id']}\n\n"
            f"Теперь пользователь может получить PvP-кит сразу.",
            parse_mode="HTML",
            reply_markup=get_admin_menu()
        )
        logger.info(f"PvP kit cooldown reset for user {user['user_id']} by admin {message.from_user.id}")
    else:
        await message.answer(
            f"❌ У пользователя @{username} нет истории получения PvP-китов для сброса.",
            reply_markup=get_admin_menu()
        )
    
    await state.clear()



