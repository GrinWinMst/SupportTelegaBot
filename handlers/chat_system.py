from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db_instance import db
from keyboards.main import get_back_to_main
from config import ADMIN_IDS, SUPPORT_STAFF_IDS
import logging
import datetime

logger = logging.getLogger(__name__)
router = Router()


class ChatStates(StatesGroup):
    chatting_in_ticket_user = State()
    chatting_in_ticket_admin = State()


@router.callback_query(F.data.startswith("chat_user_ticket_"))
async def callback_chat_user_ticket(callback: CallbackQuery, state: FSMContext):
    """Начать чат с тикетом (пользователь)"""
    await callback.answer()
    
    ticket_id = int(callback.data.split("_")[-1])
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket or ticket['user_id'] != callback.from_user.id:
        await callback.message.edit_text(
            "❌ Обращение не найдено.",
            reply_markup=get_back_to_main()
        )
        return
    
    await state.set_state(ChatStates.chatting_in_ticket_user)
    await state.update_data(ticket_id=ticket_id)
    
    await callback.message.edit_text(
        f"💬 <b>Чат с обращением #{ticket_id}</b>\n\n"
        f"Напишите ваше сообщение. Администрация получит уведомление.\n\n"
        f"Для выхода из чата нажмите /cancel",
        parse_mode="HTML"
    )


@router.message(ChatStates.chatting_in_ticket_user)
async def process_user_chat_message(message: Message, state: FSMContext):
    """Обработка сообщений от пользователя в чате"""
    if message.text and message.text.startswith('/cancel'):
        await state.clear()
        await message.answer(
            "Чат закрыт. Используйте /start для возврата в главное меню.",
            reply_markup=get_back_to_main()
        )
        return
    
    # Проверка на бан
    is_banned, ban_info = await db.is_user_banned(message.from_user.id)
    if is_banned:
        ban_text = f"🚫 <b>Вы заблокированы</b>\n\n<b>Причина:</b> {ban_info['reason']}\n"
        if ban_info['is_permanent']:
            ban_text += "\n<b>Срок:</b> Навсегда"
        else:
            ban_until = datetime.datetime.fromisoformat(ban_info['ban_until'])
            ban_text += f"\n<b>До:</b> {ban_until.strftime('%d.%m.%Y %H:%M')}"
        
        await message.answer(ban_text, parse_mode="HTML")
        await state.clear()
        return
    
    # Проверка антиспама
    can_send, wait_time = await db.check_spam(message.from_user.id, cooldown_seconds=3)
    if not can_send:
        await message.answer(
            f"⏳ Подождите еще {wait_time:.1f} секунд перед отправкой следующего сообщения."
        )
        return
    
    data = await state.get_data()
    ticket_id = data.get('ticket_id')
    
    if not ticket_id:
        await state.clear()
        await message.answer(
            "❌ Ошибка: тикет не найден.",
            reply_markup=get_back_to_main()
        )
        return
    
    # Получаем информацию о тикете
    ticket = await db.get_ticket(ticket_id)
    if not ticket:
        await state.clear()
        await message.answer("❌ Тикет не найден.", reply_markup=get_back_to_main())
        return
    
    # Проверка: закрыто ли обращение
    if ticket['status'] == 'closed':
        await state.clear()
        await message.answer(
            "🔒 Обращение закрыто! Вы можете создать новое обращение.",
            reply_markup=get_back_to_main()
        )
        return
    
    # Сохраняем сообщение
    message_text = message.text or message.caption or "[Медиа]"
    await db.add_ticket_message(ticket_id, message.from_user.id, message_text)
    await db.update_last_message(message.from_user.id)
    
    # Уведомляем только того, кто взял обращение (если взято)
    from bot import bot
    notification_text = (
        f"💬 <b>Новое сообщение в тикете #{ticket_id}</b>\n\n"
        f"<b>От:</b> @{message.from_user.username or 'Unknown'}\n"
        f"<b>Сообщение:</b> {message_text[:200]}"
    )
    
    # Если обращение назначено - уведомляем только назначенного + админов
    assigned_to = ticket.get('assigned_to')
    if assigned_to:
        # Уведомляем назначенного сотрудника (пересылаем оригинальное сообщение с медиа)
        try:
            if message.photo:
                await bot.send_photo(assigned_to, message.photo[-1].file_id, caption=notification_text, parse_mode="HTML")
            elif message.video:
                await bot.send_video(assigned_to, message.video.file_id, caption=notification_text, parse_mode="HTML")
            elif message.document:
                await bot.send_document(assigned_to, message.document.file_id, caption=notification_text, parse_mode="HTML")
            else:
                await bot.send_message(assigned_to, notification_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to notify assigned staff {assigned_to}: {e}")
        
        # Уведомляем админов
        for admin_id in ADMIN_IDS:
            if admin_id != assigned_to:
                try:
                    if message.photo:
                        await bot.send_photo(admin_id, message.photo[-1].file_id, caption=notification_text, parse_mode="HTML")
                    elif message.video:
                        await bot.send_video(admin_id, message.video.file_id, caption=notification_text, parse_mode="HTML")
                    elif message.document:
                        await bot.send_document(admin_id, message.document.file_id, caption=notification_text, parse_mode="HTML")
                    else:
                        await bot.send_message(admin_id, notification_text, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
    else:
        # Если не назначено - уведомляем всех админов и поддержку
        for admin_id in ADMIN_IDS + SUPPORT_STAFF_IDS:
            try:
                if message.photo:
                    await bot.send_photo(admin_id, message.photo[-1].file_id, caption=notification_text, parse_mode="HTML")
                elif message.video:
                    await bot.send_video(admin_id, message.video.file_id, caption=notification_text, parse_mode="HTML")
                elif message.document:
                    await bot.send_document(admin_id, message.document.file_id, caption=notification_text, parse_mode="HTML")
                else:
                    await bot.send_message(admin_id, notification_text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    await message.answer(
        "✅ Сообщение отправлено!\n\n"
        "Продолжайте писать или используйте /cancel для выхода."
    )


@router.callback_query(F.data.startswith("chat_ticket_"))
async def callback_chat_admin_ticket(callback: CallbackQuery, state: FSMContext):
    """Начать чат с тикетом (админ)"""
    if callback.from_user.id not in (ADMIN_IDS + SUPPORT_STAFF_IDS):
        await callback.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback.answer()
    
    ticket_id = int(callback.data.split("_")[-1])
    ticket = await db.get_ticket(ticket_id)
    
    if not ticket:
        await callback.message.edit_text(
            "❌ Обращение не найдено.",
            reply_markup=get_back_to_main()
        )
        return
    
    await state.set_state(ChatStates.chatting_in_ticket_admin)
    await state.update_data(ticket_id=ticket_id, ticket_user_id=ticket['user_id'])
    
    await callback.message.edit_text(
        f"💬 <b>Чат с обращением #{ticket_id}</b>\n\n"
        f"<b>Пользователь:</b> @{ticket['username']}\n\n"
        f"Напишите ваше сообщение. Пользователь получит уведомление.\n\n"
        f"Для выхода из чата нажмите /cancel",
        parse_mode="HTML"
    )


@router.message(ChatStates.chatting_in_ticket_admin)
async def process_admin_chat_message(message: Message, state: FSMContext):
    """Обработка сообщений от админа в чате"""
    if message.text and message.text.startswith('/cancel'):
        await state.clear()
        
        # Определяем роль пользователя и открываем соответствующую панель
        is_admin_user = message.from_user.id in ADMIN_IDS
        
        if is_admin_user:
            # Для админа открываем админ панель
            from keyboards.admin import get_admin_menu
            await message.answer(
                "🔧 <b>Админ панель</b>\n\n"
                "Чат закрыт. Выберите действие:",
                parse_mode="HTML",
                reply_markup=get_admin_menu()
            )
        else:
            # Для сотрудника поддержки открываем панель поддержки
            from keyboards.support import get_support_staff_menu
            open_tickets = await db.get_open_tickets()
            await message.answer(
                f"👤 <b>Панель поддержки</b>\n\n"
                f"📬 Открытых обращений: {len(open_tickets)}\n\n"
                f"Чат закрыт. Выберите действие:",
                parse_mode="HTML",
                reply_markup=get_support_staff_menu()
            )
        return
    
    data = await state.get_data()
    ticket_id = data.get('ticket_id')
    ticket_user_id = data.get('ticket_user_id')
    
    if not ticket_id or not ticket_user_id:
        await state.clear()
        await message.answer("❌ Ошибка: тикет не найден.")
        return
    
    # Сохраняем сообщение
    message_text = message.text or message.caption or "[Медиа]"
    await db.add_ticket_message(ticket_id, message.from_user.id, message_text)
    
    # Уведомляем пользователя (с медиа если есть)
    from bot import bot
    try:
        caption_text = f"💬 <b>Ответ администрации на обращение #{ticket_id}:</b>\n\n{message_text}"
        
        if message.photo:
            await bot.send_photo(ticket_user_id, message.photo[-1].file_id, caption=caption_text, parse_mode="HTML")
        elif message.video:
            await bot.send_video(ticket_user_id, message.video.file_id, caption=caption_text, parse_mode="HTML")
        elif message.document:
            await bot.send_document(ticket_user_id, message.document.file_id, caption=caption_text, parse_mode="HTML")
        else:
            await bot.send_message(ticket_user_id, caption_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify user {ticket_user_id}: {e}")
        await message.answer("⚠️ Не удалось отправить уведомление пользователю.")
    
    await message.answer(
        "✅ Сообщение отправлено пользователю!\n\n"
        "Продолжайте писать или используйте /cancel для выхода."
    )


# Глобальный обработчик для сообщений вне контекста
@router.message()
async def handle_unknown_message(message: Message):
    """Обработка сообщений, отправленных вне контекста чата или команд"""
    # Игнорируем команды - они обрабатываются другими хендлерами
    if message.text and message.text.startswith('/'):
        return
    
    # Сообщаем, что сообщение не было доставлено
    await message.answer(
        "❌ <b>Ваше сообщение не было никуда доставлено.</b>\n\n"
        "Используйте /start для возврата в главное меню.",
        parse_mode="HTML"
    )

