from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db_instance import db
from rcon_manager import RconManager
from keyboards.main import get_main_menu, get_back_to_main
import logging

logger = logging.getLogger(__name__)
router = Router()


class PvPKitStates(StatesGroup):
    waiting_for_nickname = State()


async def check_channel_subscriptions(user_id: int) -> tuple[bool, str]:
    """
    Проверка подписки на обязательные каналы
    
    Returns:
        (bool, str): (подписан ли, сообщение об ошибке или пустая строка)
    """
    channels = await db.get_required_channels()
    
    if not channels:
        return True, ""  # Нет обязательных каналов
    
    from bot import bot
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    not_subscribed = []
    
    for channel in channels:
        try:
            member = await bot.get_chat_member(channel['channel_id'], user_id)
            logger.info(f"PvP Kit - Subscription check for user {user_id} in channel {channel['channel_id']}: status={member.status}")
            
            # Проверяем статус: member, administrator, creator - это подписан
            # left, kicked - это не подписан
            if member.status in ['left', 'kicked', 'restricted']:
                logger.warning(f"User {user_id} is NOT subscribed to {channel['channel_id']} (status: {member.status})")
                not_subscribed.append(channel)
            elif member.status not in ['member', 'administrator', 'creator']:
                logger.warning(f"User {user_id} has unknown status in {channel['channel_id']}: {member.status}")
                not_subscribed.append(channel)
        except Exception as e:
            logger.error(f"Failed to check subscription for {channel['channel_id']}: {e}")
            # В случае ошибки добавляем канал как не подписанный (более строгая проверка)
            not_subscribed.append(channel)
    
    if not_subscribed:
        text = "❌ <b>Для получения PvP-набора необходимо подписаться на наши каналы:</b>\n\n"
        buttons = []
        
        for channel in not_subscribed:
            text += f"• {channel['channel_name']}\n"
            if channel['channel_url']:
                buttons.append([InlineKeyboardButton(
                    text=f"📺 {channel['channel_name']}", 
                    url=channel['channel_url']
                )])
        
        text += "\nПосле подписки попробуйте снова!"
        
        logger.info(f"User {user_id} is missing subscriptions to {len(not_subscribed)} channels")
        return False, text
    
    logger.info(f"User {user_id} is subscribed to all required channels")
    return True, ""


@router.callback_query(F.data == "pvp_kit")
async def callback_pvp_kit(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки получения PvP-кита"""
    await callback.answer()
    await db.add_user(callback.from_user.id, callback.from_user.username)
    
    # Проверяем, включена ли функция
    is_enabled = await db.is_pvp_kit_enabled()
    if not is_enabled:
        await callback.message.edit_text(
            "❌ <b>Функция получения бесплатных PvP-наборов временно отключена.</b>\n\n"
            "Попробуйте позже!",
            parse_mode="HTML",
            reply_markup=get_back_to_main()
        )
        return
    
    # Проверяем подписку на каналы
    is_subscribed, subscription_message = await check_channel_subscriptions(callback.from_user.id)
    
    if not is_subscribed:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        channels = await db.get_required_channels()
        buttons = []
        
        for channel in channels:
            if channel['channel_url']:
                buttons.append([InlineKeyboardButton(
                    text=f"📺 {channel['channel_name']}", 
                    url=channel['channel_url']
                )])
        
        buttons.append([InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="pvp_kit")])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
        
        await callback.message.edit_text(
            subscription_message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        return
    
    # Проверяем, может ли пользователь получить кит
    can_claim, next_time = await db.can_claim_pvp_kit(callback.from_user.id)
    
    if not can_claim:
        await callback.message.edit_text(
            f"⏳ <b>PvP-набор пока недоступен!</b>\n\n"
            f"Следующий набор можно будет получить: <b>{next_time}</b>\n\n"
            f"⚠️ Вы можете получать бесплатный PvP-набор каждые 24 часа!",
            parse_mode="HTML",
            reply_markup=get_back_to_main()
        )
        return
    
    # Запрашиваем ник
    await callback.message.edit_text(
        "⚔️ <b>Получение бесплатного PvP-набора</b>\n\n"
        "Вы получите временный доступ к бесплатным PvP-наборам на сервере!\n\n"
        "<b>Введите ваш игровой ник на сервере:</b>",
        parse_mode="HTML",
        reply_markup=get_back_to_main()
    )
    
    await state.set_state(PvPKitStates.waiting_for_nickname)


@router.message(PvPKitStates.waiting_for_nickname)
async def process_nickname_for_pvp_kit(message: Message, state: FSMContext):
    """Обработка ввода ника для получения PvP-кита"""
    minecraft_nickname = message.text.strip()
    
    # Проверяем, может ли пользователь получить кит
    can_claim, _ = await db.can_claim_pvp_kit(message.from_user.id)
    
    if not can_claim:
        await message.answer(
            "❌ Вы уже недавно получали PvP-набор. Попробуйте позже.",
            reply_markup=get_back_to_main()
        )
        await state.clear()
        return
    
    # Регистрируем получение
    success = await db.claim_pvp_kit(message.from_user.id, minecraft_nickname)
    
    if not success:
        await message.answer(
            "❌ Произошла ошибка при регистрации. Попробуйте позже.",
            reply_markup=get_back_to_main()
        )
        await state.clear()
        return
    
    # Выдаем разрешение через RCON
    command = f"kit give free {minecraft_nickname}"
    rcon_success = await RconManager.execute_command(command)
    if rcon_success:
        text = (
            "🎉 <b>Поздравляю!</b> 🎉\n\n"
            "Вам был выдан набор FREE!\n\n"
            "🔄 Следующий набор можно будет получить через 1 день!"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_to_main())
        logger.info(f"PvP kit claimed: user_id={message.from_user.id}, nickname={minecraft_nickname}")
    else:
        text = (
            "⚠️ Получение зарегистрировано, но возникла ошибка при выдаче разрешения на сервере.\n"
            "Свяжитесь с администрацией."
        )
        await message.answer(text, reply_markup=get_back_to_main())
    
    await state.clear()
