from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db_instance import db
from keyboards.admin import get_ban_duration_keyboard, get_banned_users_keyboard
from keyboards.main import get_back_to_main
from config import ADMIN_IDS, SUPPORT_STAFF_IDS
import logging
import datetime

logger = logging.getLogger(__name__)
router = Router()


class BanStates(StatesGroup):
    """Состояния для процесса бана"""
    selecting_duration = State()
    entering_reason = State()


class ProgressResetStates(StatesGroup):
    """Состояния для сброса прогресса"""
    entering_nickname = State()


# ===== БАН ПОЛЬЗОВАТЕЛЕЙ =====
@router.callback_query(F.data.startswith("ban_user_"))
async def callback_ban_user(callback: CallbackQuery, state: FSMContext):
    """Начало процесса бана пользователя"""
    await callback.answer()
    
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SUPPORT_STAFF_IDS:
        await callback.answer("❌ У вас нет доступа к этой функции!", show_alert=True)
        return
    
    # Извлекаем ID пользователя и ID тикета
    parts = callback.data.split("_")
    target_user_id = int(parts[2])
    ticket_id = int(parts[3]) if len(parts) > 3 else None
    
    # Сохраняем данные
    await state.update_data(
        target_user_id=target_user_id,
        ticket_id=ticket_id,
        banner_id=user_id
    )
    await state.set_state(BanStates.selecting_duration)
    
    await callback.message.edit_text(
        f"⏱ <b>Выберите длительность бана для пользователя {target_user_id}:</b>",
        parse_mode="HTML",
        reply_markup=get_ban_duration_keyboard()
    )


@router.callback_query(BanStates.selecting_duration, F.data.startswith("ban_duration_"))
async def callback_select_ban_duration(callback: CallbackQuery, state: FSMContext):
    """Выбор длительности бана"""
    await callback.answer()
    
    duration_str = callback.data.split("_")[2]
    
    # Преобразуем в часы или None для пермабана
    duration_hours = None
    if duration_str == "3h":
        duration_hours = 3
        duration_text = "3 часа"
    elif duration_str == "1d":
        duration_hours = 24
        duration_text = "1 день"
    elif duration_str == "1w":
        duration_hours = 168
        duration_text = "1 неделю"
    elif duration_str == "permanent":
        duration_hours = None
        duration_text = "навсегда"
    else:
        await callback.answer("❌ Неверная длительность!", show_alert=True)
        await state.clear()
        return
    
    await state.update_data(
        ban_duration=duration_hours,
        duration_text=duration_text
    )
    await state.set_state(BanStates.entering_reason)
    
    await callback.message.edit_text(
        f"📝 <b>Длительность:</b> {duration_text}\n\n"
        f"<b>Теперь напишите причину бана:</b>",
        parse_mode="HTML"
    )


@router.message(BanStates.entering_reason)
async def process_ban_reason(message: Message, state: FSMContext):
    """Обработка причины бана"""
    reason = message.text
    if not reason or len(reason) < 3:
        await message.answer("❌ Причина бана должна содержать минимум 3 символа.")
        return
    
    data = await state.get_data()
    target_user_id = data['target_user_id']
    banner_id = data['banner_id']
    ban_duration = data['ban_duration']
    duration_text = data['duration_text']
    ticket_id = data.get('ticket_id')
    
    # Баним пользователя
    await db.ban_user(target_user_id, banner_id, reason, ban_duration)
    
    # Уведомление администратору
    from bot import bot
    ban_text = (
        f"✅ <b>Пользователь заблокирован!</b>\n\n"
        f"<b>User ID:</b> {target_user_id}\n"
        f"<b>Длительность:</b> {duration_text}\n"
        f"<b>Причина:</b> {reason}\n"
        f"<b>Кем заблокирован:</b> @{message.from_user.username or 'Unknown'}"
    )
    
    await message.answer(ban_text, parse_mode="HTML")
    
    # Уведомляем всех администраторов
    for admin_id in ADMIN_IDS:
        if admin_id != banner_id:
            try:
                await bot.send_message(
                    admin_id,
                    f"🚨 <b>Новый бан!</b>\n\n{ban_text}",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    # Уведомляем забаненного пользователя
    try:
        user_ban_text = (
            f"🚫 <b>Вы были заблокированы</b>\n\n"
            f"<b>Причина:</b> {reason}\n"
            f"<b>Срок:</b> {duration_text}"
        )
        if ticket_id:
            user_ban_text += f"\n<b>Обращение:</b> #{ticket_id}"
        
        await bot.send_message(target_user_id, user_ban_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify banned user {target_user_id}: {e}")
    
    await state.clear()


# ===== УПРАВЛЕНИЕ БАНАМИ =====
@router.callback_query(F.data == "admin_bans")
async def callback_admin_bans(callback: CallbackQuery):
    """Меню управления банами"""
    await callback.answer()
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет доступа к этой функции!", show_alert=True)
        return
    
    banned_users = await db.get_banned_users()
    
    if not banned_users:
        await callback.message.edit_text(
            "✅ <b>Забаненных пользователей нет</b>",
            parse_mode="HTML",
            reply_markup=get_back_to_main()
        )
        return
    
    await callback.message.edit_text(
        f"🚫 <b>Забаненные пользователи ({len(banned_users)}):</b>\n\n"
        f"Выберите пользователя для разбана:",
        parse_mode="HTML",
        reply_markup=get_banned_users_keyboard(banned_users)
    )


@router.callback_query(F.data.startswith("unban_"))
async def callback_unban_user(callback: CallbackQuery):
    """Разбанить пользователя"""
    await callback.answer()
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет доступа к этой функции!", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[1])
    
    await db.unban_user(user_id)
    
    # Уведомляем
    from bot import bot
    try:
        await bot.send_message(
            user_id,
            "✅ <b>Вы были разблокированы!</b>\n\nТеперь вы можете создавать обращения.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to notify unbanned user {user_id}: {e}")
    
    await callback.message.edit_text(
        f"✅ <b>Пользователь {user_id} разблокирован!</b>",
        parse_mode="HTML",
        reply_markup=get_back_to_main()
    )


# ===== СБРОС ПРОГРЕССА =====
@router.callback_query(F.data == "admin_reset_progress")
async def callback_admin_reset_progress(callback: CallbackQuery, state: FSMContext):
    """Начало процесса сброса прогресса"""
    await callback.answer()
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет доступа к этой функции!", show_alert=True)
        return
    
    await state.set_state(ProgressResetStates.entering_nickname)
    
    await callback.message.edit_text(
        "🎮 <b>Сброс задержки награды</b>\n\n"
        "Напишите telegram username игрока (например: @username или username):",
        parse_mode="HTML"
    )


@router.message(ProgressResetStates.entering_nickname)
async def process_reset_nickname(message: Message, state: FSMContext):
    """Обработка telegram username для сброса прогресса"""
    username = message.text.strip()
    
    if not username:
        await message.answer("❌ Введите корректный username!")
        return
    
    # Ищем пользователя по telegram username
    user = await db.get_user_by_telegram_username(username)
    
    if not user:
        await message.answer(
            f"❌ <b>Пользователь '{username}' не найден в базе данных.</b>\n\n"
            f"Убедитесь, что пользователь запускал бота хотя бы раз.",
            parse_mode="HTML",
            reply_markup=get_back_to_main()
        )
        await state.clear()
        return
    
    # Получаем прогресс наград
    user_progress = await db.get_reward_progress(user['user_id'])
    
    if not user_progress:
        await message.answer(
            f"❌ <b>У пользователя '@{user['username']}' нет прогресса наград.</b>\n\n"
            f"Возможно, он еще ни разу не забирал награды.",
            parse_mode="HTML",
            reply_markup=get_back_to_main()
        )
        await state.clear()
        return
    
    # Сбрасываем кулдаун
    success = await db.reset_reward_cooldown(user['user_id'])
    
    if success:
        # Уведомляем пользователя
        from bot import bot
        try:
            await bot.send_message(
                user['user_id'],
                "🎁 <b>Администратор сбросил задержку на получение награды!</b>\n\n"
                "Вы можете забрать следующую награду прямо сейчас!",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {user['user_id']}: {e}")
        
        await message.answer(
            f"✅ <b>Задержка сброшена!</b>\n\n"
            f"<b>Telegram:</b> @{user['username']}\n"
            f"<b>User ID:</b> {user['user_id']}\n"
            f"<b>Текущий уровень награды:</b> {user_progress['current_level']}\n\n"
            f"Игрок может забрать следующую награду сразу!",
            parse_mode="HTML",
            reply_markup=get_back_to_main()
        )
    else:
        await message.answer(
            "❌ Не удалось сбросить задержку. Попробуйте позже.",
            reply_markup=get_back_to_main()
        )
    
    await state.clear()

