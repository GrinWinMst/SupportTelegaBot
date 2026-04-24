from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db_instance import db
from rcon_manager import RconManager
from keyboards.main import get_main_menu, get_back_to_main, get_reward_confirmation
from config import DAILY_REWARDS
import logging

logger = logging.getLogger(__name__)
router = Router()


class RewardStates(StatesGroup):
    waiting_for_nickname = State()


async def format_rewards_table(user_id: int = None) -> str:
    """Форматирование таблицы наград с отметками"""
    text = "📋 <b>Ежедневные награды:</b>\n\n"
    
    current_level = 0
    if user_id:
        progress = await db.get_reward_progress(user_id)
        if progress:
            current_level = progress['current_level']
    
    for reward in DAILY_REWARDS:
        # Добавляем галочку если награда уже забрана
        if reward['day'] <= current_level:
            text += f"✅ День {reward['day']}: {reward['description']}\n"
        else:
            text += f"⬜ День {reward['day']}: {reward['description']}\n"
    
    text += "\n⚠️ <b>Важно:</b> Если пропустить день - прогресс сбросится!"
    return text


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
            logger.info(f"Subscription check for user {user_id} in channel {channel['channel_id']}: status={member.status}")
            
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
        text = "❌ <b>Для получения наград необходимо подписаться на наши каналы:</b>\n\n"
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


@router.message(F.text.startswith("!халява"))
async def command_freebie(message: Message):
    """Обработка команды !халява <ник>"""
    await db.add_user(message.from_user.id, message.from_user.username)
    
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer(
            "❌ <b>Неверный формат команды!</b>\n\n"
            "Используйте: <code>!халява ваш_ник</code>\n\n"
            "Например: <code>!халява Steve</code>",
            parse_mode="HTML"
        )
        return
    
    minecraft_nickname = parts[1].strip()
    
    # Проверяем подписку на каналы
    is_subscribed, subscription_message = await check_channel_subscriptions(message.from_user.id)
    
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
        
        buttons.append([InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="daily_reward")])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
        
        await message.answer(
            subscription_message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        return
    
    # Проверяем, может ли пользователь забрать награду
    can_claim, status = await db.can_claim_reward(message.from_user.id)
    
    if not can_claim:
        progress = await db.get_reward_progress(message.from_user.id)
        rewards_table = await format_rewards_table(message.from_user.id)
        await message.answer(
            f"⏳ <b>Награда пока недоступна!</b>\n\n"
            f"Ваш текущий уровень: {progress['current_level']}/7\n"
            f"Следующая награда будет доступна: <b>{status}</b>\n\n"
            f"{rewards_table}",
            parse_mode="HTML",
            reply_markup=get_back_to_main()
        )
        return
    
    # Забираем награду
    reward_level = await db.claim_reward(message.from_user.id, minecraft_nickname)
    
    if reward_level == -1:
        await message.answer(
            "❌ Произошла ошибка при получении награды. Попробуйте позже.",
            reply_markup=get_back_to_main()
        )
        return
    
    # Выдаем награду на сервере
    reward_config = DAILY_REWARDS[reward_level - 1]
    success = await RconManager.give_reward(minecraft_nickname, reward_config['command'])
    
    if success:
        if reward_level == 7:
            text = (
                f"🎉 <b>ПОЗДРАВЛЯЕМ!</b> 🎉\n\n"
                f"Вы получили максимальную награду!\n"
                f"{reward_config['description']}\n\n"
                f"Завтра прогресс начнется заново.\n"
                f"Продолжайте забирать награды каждый день! 🔥"
            )
        else:
            text = (
                f"✅ <b>Награда получена!</b>\n\n"
                f"Уровень награды: {reward_level}/7\n"
                f"Получено: {reward_config['description']}\n\n"
                f"⏰ Возвращайтесь через 24 часа, чтобы забрать следующую награду!\n\n"
                f"⚠️ Не забудьте забрать награду вовремя, иначе прогресс сбросится!"
            )
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_to_main())
        logger.info(f"Reward claimed: user_id={message.from_user.id}, level={reward_level}, nickname={minecraft_nickname}")
    else:
        await message.answer(
            "⚠️ Награда зарегистрирована, но возникла ошибка при выдаче на сервере.\n"
            "Свяжитесь с администрацией.",
            reply_markup=get_back_to_main()
        )


@router.callback_query(F.data == "daily_reward")
async def callback_daily_reward(callback: CallbackQuery, state: FSMContext):
    """Кнопка забора ежедневной награды"""
    await callback.answer()
    await db.add_user(callback.from_user.id, callback.from_user.username)
    
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
        
        buttons.append([InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="daily_reward")])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
        
        await callback.message.edit_text(
            subscription_message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        return
    
    # Проверяем, может ли пользователь забрать награду
    can_claim, status = await db.can_claim_reward(callback.from_user.id)
    progress = await db.get_reward_progress(callback.from_user.id)
    
    if not can_claim:
        rewards_table = await format_rewards_table(callback.from_user.id)
        await callback.message.edit_text(
            f"⏳ <b>Награда пока недоступна!</b>\n\n"
            f"Ваш текущий уровень: {progress['current_level']}/7\n"
            f"Следующая награда будет доступна: <b>{status}</b>\n\n"
            f"{rewards_table}",
            parse_mode="HTML",
            reply_markup=get_back_to_main()
        )
        return
    
    # Определяем следующий уровень награды
    if not progress or status == "reset":
        next_level = 1
    else:
        # После 7-го дня сбрасываем на 1-й
        next_level = (progress['current_level'] % 7) + 1
    
    reward_config = DAILY_REWARDS[next_level - 1]
    rewards_table = await format_rewards_table(callback.from_user.id)
    
    await callback.message.edit_text(
        f"🎁 <b>Доступна награда уровня {next_level}/7!</b>\n\n"
        f"Вы получите: {reward_config['description']}\n\n"
        f"{rewards_table}\n\n"
        f"<b>Введите ваш ник на сервере:</b>",
        parse_mode="HTML",
        reply_markup=get_back_to_main()
    )
    
    await state.set_state(RewardStates.waiting_for_nickname)
    await state.update_data(next_level=next_level)


@router.message(RewardStates.waiting_for_nickname)
async def process_nickname_for_reward(message: Message, state: FSMContext):
    """Обработка ввода ника для получения награды"""
    minecraft_nickname = message.text.strip()
    data = await state.get_data()
    next_level = data.get('next_level', 1)
    
    # Забираем награду
    reward_level = await db.claim_reward(message.from_user.id, minecraft_nickname)
    
    if reward_level == -1:
        await message.answer(
            "❌ Произошла ошибка при получении награды. Попробуйте позже.",
            reply_markup=get_back_to_main()
        )
        await state.clear()
        return
    
    # Выдаем награду на сервере
    reward_config = DAILY_REWARDS[reward_level - 1]
    success = await RconManager.give_reward(minecraft_nickname, reward_config['command'])
    
    if success:
        if reward_level == 7:
            text = (
                f"🎉 <b>ПОЗДРАВЛЯЕМ!</b> 🎉\n\n"
                f"Вы получили максимальную награду!\n"
                f"{reward_config['description']}\n\n"
                f"Завтра прогресс начнется заново.\n"
                f"Продолжайте забирать награды каждый день! 🔥"
            )
        else:
            text = (
                f"✅ <b>Награда получена!</b>\n\n"
                f"Уровень награды: {reward_level}/7\n"
                f"Получено: {reward_config['description']}\n\n"
                f"⏰ Возвращайтесь через 24 часа, чтобы забрать следующую награду!\n\n"
                f"⚠️ Не забудьте забрать награду вовремя, иначе прогресс сбросится!"
            )
        
        await message.answer(text, parse_mode="HTML", reply_markup=get_back_to_main())
        logger.info(f"Reward claimed: user_id={message.from_user.id}, level={reward_level}, nickname={minecraft_nickname}")
    else:
        await message.answer(
            "⚠️ Награда зарегистрирована, но возникла ошибка при выдаче на сервере.\n"
            "Свяжитесь с администрацией.",
            reply_markup=get_back_to_main()
        )
    
    await state.clear()


@router.callback_query(F.data == "my_rewards")
async def callback_my_rewards(callback: CallbackQuery):
    """Показать информацию о наградах пользователя"""
    await callback.answer()
    
    progress = await db.get_reward_progress(callback.from_user.id)
    rewards_table = await format_rewards_table(callback.from_user.id)
    
    if not progress:
        await callback.message.edit_text(
            f"📋 <b>Ваши награды</b>\n\n"
            f"Вы еще не получали награды.\n"
            f"Используйте команду <code>!халява ваш_ник</code> или нажмите кнопку ниже!\n\n"
            f"{rewards_table}",
            parse_mode="HTML",
            reply_markup=get_main_menu()
        )
        return
    
    can_claim, status = await db.can_claim_reward(callback.from_user.id)
    
    if can_claim:
        status_text = "✅ <b>Награда доступна прямо сейчас!</b>"
    else:
        status_text = f"⏳ Следующая награда: <b>{status}</b>"
    
    await callback.message.edit_text(
        f"📋 <b>Ваши награды</b>\n\n"
        f"Текущий уровень: {progress['current_level']}/7\n"
        f"Ник на сервере: {progress['minecraft_nickname']}\n\n"
        f"{status_text}\n\n"
        f"{rewards_table}",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )

