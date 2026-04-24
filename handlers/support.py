from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db_instance import db
from keyboards.support import (
    get_support_menu, get_media_type_menu, get_form_submit_menu,
    get_after_submit_menu, get_cancel_form_button
)
from keyboards.main import get_back_to_main
from config import TICKET_TYPES, ADMIN_IDS, SUPPORT_STAFF_IDS
import logging

logger = logging.getLogger(__name__)
router = Router()


class FormStates(StatesGroup):
    # Медиа TikTok
    media_tiktok_nickname = State()
    media_tiktok_channel = State()
    media_tiktok_confirm = State()
    
    # Медиа YouTube
    media_youtube_nickname = State()
    media_youtube_channel = State()
    media_youtube_confirm = State()
    
    # Хелпер
    helper_nickname = State()
    helper_age = State()
    helper_vk = State()
    helper_telegram = State()
    helper_discord = State()
    helper_playtime = State()
    helper_wipe_playtime = State()
    helper_duties = State()
    helper_experience = State()
    helper_confirm = State()
    
    # Вопрос
    question_nickname = State()
    question_text = State()
    question_confirm = State()
    
    # Жалоба на игрока
    player_complaint_nickname = State()
    player_complaint_violator = State()
    player_complaint_rule = State()
    player_complaint_proof = State()
    player_complaint_confirm = State()
    
    # Жалоба на администрацию
    admin_complaint_nickname = State()
    admin_complaint_admin = State()
    admin_complaint_rule = State()
    admin_complaint_proof = State()
    admin_complaint_confirm = State()
    
    # Баг/Дюп
    bug_nickname = State()
    bug_description = State()
    bug_proof = State()
    bug_confirm = State()
    
    # Другое
    other_text = State()
    other_confirm = State()
    
    # Общение в тикете
    chatting_in_ticket = State()


# Тексты для разных типов медиа
MEDIA_TEXTS = {
    "tiktok": """📱 <b>Заявка на медиа (TikTok)</b>

Мы рады, что вы захотели присоединиться к нам! Пожалуйста, заполните форму подачи заявки:

1. Ваш ник на сервере
2. Ссылка на ваш канал

Если вы уже снимали и у вас есть просмотры на канале - можете сразу подавать заявку.

<b>Иначе нужно выполнить условия:</b>

1️⃣ Сними 3 ролика по серверу The Dawn Project
2️⃣ Каждый ролик должен набрать от 500 просмотров

🎁 После этого — мы выдадим тебе привилегию TIKTOK!

💸 <b>А вот за просмотры ты получаешь награды:</b>
• 500 просмотров → 50 аврор
• 1000 просмотров → 100 аврор
• 5000 просмотров → 500 аврор
• 10 000 просмотров → 1000 аврор

🔥 А если у тебя будет большой актив и хорошие просмотры — ты сможешь стать МЕДИА проекта и получать реальные деньги 💰

📋 <b>Критерии для канала:</b>
• На канале нет рекламы читов
• В описании канала указано: Играю тут: tt.the-dawn.ru

🎬 <b>Критерии для роликов:</b>
• Ролик должен быть снят на сервере The Dawn Project
• В ролике не должно быть рекламы читов и других серверов
• В названии и на экране (минимум 5 секунд) должен быть IP: tt.the-dawn.ru
• Обязательно тег #thedawnproject

<b>Введите ваш ник на сервере:</b>""",
    
    "youtube": """🎬 <b>Заявка на медиа (YouTube)</b>

Мы рады, что вы захотели присоединиться к нам! Пожалуйста, заполните форму подачи заявки:

1. Ваш ник на сервере
2. Ссылка на ваш канал

Если вы уже снимали и у вас есть просмотры на канале - можете сразу подавать заявку.

<b>Иначе нужно выполнить условия:</b>

Мы запустили новую привилегию — YOUTUBE 💫
Получить её может каждый, кто готов немного поснимать контент про наш сервер!

1️⃣ Сними 1 ролик по серверу The Dawn Project
2️⃣ Ролик должен набрать 300 просмотров

🎁 После этого — мы выдадим тебе привилегию YOUTUBE!

💸 <b>А вот за просмотры ты получаешь награды:</b>
• 300 просмотров → 150 аврор
• 500 просмотров → 500 аврор
• 1000 просмотров → 1000 аврор
• 5000 просмотров → 10.000 аврор

🔥 А если у тебя будет большой актив и хорошие просмотры — ты сможешь стать МЕДИА проекта и получать реальные деньги 💰

📋 <b>Критерии для канала:</b>
• На канале нет рекламы читов

🎬 <b>Критерии для роликов:</b>
1) Ролик должен быть снят на сервере The Dawn Project
2) В ролике не должно быть рекламы читов и других серверов
4) В названии должно быть указано название сервер The Dawn Project
5) Длинна ролика должна быть не менее 8-ми минут
6) В описании под роликом должно быть:

Играю всегда тут:
• play.the-dawn.ru — основной сервер
• ua.the-dawn.fans — для игроков из-за границы
• Сайт: the-dawn.ru
• Telegram: https://t.me/thedawnTG
• ВКонтакте: https://vk.com/thedawnvk
• Discord: https://discord.gg/7bkt6Xm8Dc

Обязательно тег #thedawnproject

<b>Введите ваш ник на сервере:</b>"""
}


@router.callback_query(F.data == "support_menu")
async def callback_support_menu(callback: CallbackQuery):
    """Меню поддержки"""
    await callback.answer()
    await callback.message.edit_text(
        "💬 <b>Поддержка</b>\n\n"
        "Выберите тип обращения:",
        parse_mode="HTML",
        reply_markup=get_support_menu()
    )


@router.callback_query(F.data == "support_media")
async def callback_support_media(callback: CallbackQuery):
    """Выбор типа медиа"""
    await callback.answer()
    await callback.message.edit_text(
        "📺 <b>Подать заявку на медиа</b>\n\n"
        "Выберите вашу платформу:",
        parse_mode="HTML",
        reply_markup=get_media_type_menu()
    )


# ===== МЕДИА TIKTOK =====
@router.callback_query(F.data == "media_tiktok")
async def callback_media_tiktok(callback: CallbackQuery, state: FSMContext):
    """Начало заполнения формы TikTok"""
    await callback.answer()
    await callback.message.edit_text(
        MEDIA_TEXTS["tiktok"],
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.media_tiktok_nickname)


@router.message(FormStates.media_tiktok_nickname)
async def process_tiktok_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer(
        "<b>Отлично!</b>\n\nТеперь отправьте ссылку на ваш канал:",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.media_tiktok_channel)


@router.message(FormStates.media_tiktok_channel)
async def process_tiktok_channel(message: Message, state: FSMContext):
    await state.update_data(channel=message.text)
    data = await state.get_data()
    
    form_text = f"""📋 <b>Проверьте вашу заявку:</b>

<b>Тип:</b> Заявка на медиа (TikTok)
<b>Ник на сервере:</b> {data['nickname']}
<b>Ссылка на канал:</b> {data['channel']}

Перепроверьте вашу заявку и нажмите на кнопку "отправить"
Если вы что-то не написали, переделайте заявку и отправьте её ещё раз."""
    
    await message.answer(
        form_text,
        parse_mode="HTML",
        reply_markup=get_form_submit_menu("support_media")
    )
    await state.set_state(FormStates.media_tiktok_confirm)


# ===== МЕДИА YOUTUBE =====
@router.callback_query(F.data == "media_youtube")
async def callback_media_youtube(callback: CallbackQuery, state: FSMContext):
    """Начало заполнения формы YouTube"""
    await callback.answer()
    await callback.message.edit_text(
        MEDIA_TEXTS["youtube"],
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.media_youtube_nickname)


@router.message(FormStates.media_youtube_nickname)
async def process_youtube_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer(
        "<b>Отлично!</b>\n\nТеперь отправьте ссылку на ваш канал:",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.media_youtube_channel)


@router.message(FormStates.media_youtube_channel)
async def process_youtube_channel(message: Message, state: FSMContext):
    await state.update_data(channel=message.text)
    data = await state.get_data()
    
    form_text = f"""📋 <b>Проверьте вашу заявку:</b>

<b>Тип:</b> Заявка на медиа (YouTube)
<b>Ник на сервере:</b> {data['nickname']}
<b>Ссылка на канал:</b> {data['channel']}

Перепроверьте вашу заявку и нажмите на кнопку "отправить"
Если вы что-то не написали, переделайте заявку и отправьте её ещё раз."""
    
    await message.answer(
        form_text,
        parse_mode="HTML",
        reply_markup=get_form_submit_menu("support_media")
    )
    await state.set_state(FormStates.media_youtube_confirm)


# ===== ХЕЛПЕР =====
@router.callback_query(F.data == "support_helper")
async def callback_support_helper(callback: CallbackQuery, state: FSMContext):
    """Начало заполнения формы на хелпера"""
    await callback.answer()
    await callback.message.edit_text(
        "👮 <b>Заявка на хелпера</b>\n\n"
        "Мы рады, что вы захотели присоединиться к нам! Пожалуйста, заполните форму подачи заявки:\n\n"
        "<b>1. Ваш игровой ник</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.helper_nickname)


@router.message(FormStates.helper_nickname)
async def process_helper_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer(
        "<b>2. Ваш возраст</b> (понадобится подтверждающий документ):",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.helper_age)


@router.message(FormStates.helper_age)
async def process_helper_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await message.answer(
        "<b>3. Ссылка на основной аккаунт ВКонтакте:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.helper_vk)


@router.message(FormStates.helper_vk)
async def process_helper_vk(message: Message, state: FSMContext):
    await state.update_data(vk=message.text)
    await message.answer(
        "<b>4. Ссылка на основной аккаунт Telegram:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.helper_telegram)


@router.message(FormStates.helper_telegram)
async def process_helper_telegram(message: Message, state: FSMContext):
    await state.update_data(telegram=message.text)
    await message.answer(
        "<b>5. Ссылка на основной аккаунт Discord:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.helper_discord)


@router.message(FormStates.helper_discord)
async def process_helper_discord(message: Message, state: FSMContext):
    await state.update_data(discord=message.text)
    await message.answer(
        "<b>6. Сколько всего вы играете на проекте:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.helper_playtime)


@router.message(FormStates.helper_playtime)
async def process_helper_playtime(message: Message, state: FSMContext):
    await state.update_data(playtime=message.text)
    await message.answer(
        "<b>7. Сколько вы наиграли в этом вайпе:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.helper_wipe_playtime)


@router.message(FormStates.helper_wipe_playtime)
async def process_helper_wipe_playtime(message: Message, state: FSMContext):
    await state.update_data(wipe_playtime=message.text)
    await message.answer(
        "<b>8. Как вы представляете свои обязанности в роли помощника/модератора:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.helper_duties)


@router.message(FormStates.helper_duties)
async def process_helper_duties(message: Message, state: FSMContext):
    await state.update_data(duties=message.text)
    await message.answer(
        "<b>9. Был ли у вас опыт на других серверах? Перечислите их:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.helper_experience)


@router.message(FormStates.helper_experience)
async def process_helper_experience(message: Message, state: FSMContext):
    await state.update_data(experience=message.text)
    data = await state.get_data()
    
    form_text = f"""📋 <b>Проверьте вашу заявку:</b>

<b>Тип:</b> Заявка на хелпера
<b>1. Игровой ник:</b> {data['nickname']}
<b>2. Возраст:</b> {data['age']}
<b>3. ВКонтакте:</b> {data['vk']}
<b>4. Telegram:</b> {data['telegram']}
<b>5. Discord:</b> {data['discord']}
<b>6. Общее время на проекте:</b> {data['playtime']}
<b>7. Время в этом вайпе:</b> {data['wipe_playtime']}
<b>8. Представление обязанностей:</b> {data['duties']}
<b>9. Опыт на других серверах:</b> {data['experience']}

Перепроверьте вашу заявку и нажмите на кнопку "отправить"
Если вы что-то не написали, переделайте заявку и отправьте её ещё раз."""
    
    await message.answer(
        form_text,
        parse_mode="HTML",
        reply_markup=get_form_submit_menu("support_menu")
    )
    await state.set_state(FormStates.helper_confirm)


# ===== ВОПРОС ПО СЕРВЕРУ =====
@router.callback_query(F.data == "support_question")
async def callback_support_question(callback: CallbackQuery, state: FSMContext):
    """Вопрос по серверу"""
    await callback.answer()
    await callback.message.edit_text(
        "❓ <b>Вопрос по серверу</b>\n\n"
        "Пожалуйста, заполните форму:\n\n"
        "<b>1. Ваш игровой ник:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.question_nickname)


@router.message(FormStates.question_nickname)
async def process_question_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer(
        "<b>2. Максимально подробно распишите ваш вопрос в 1 сообщении:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.question_text)


@router.message(FormStates.question_text)
async def process_question_text(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    data = await state.get_data()
    
    form_text = f"""📋 <b>Проверьте вашу заявку:</b>

<b>Тип:</b> Вопрос по серверу
<b>Ник:</b> {data['nickname']}
<b>Вопрос:</b> {data['question']}

Перепроверьте вашу заявку и нажмите на кнопку "отправить"
Если вы что-то не написали, переделайте заявку и отправьте её ещё раз."""
    
    await message.answer(
        form_text,
        parse_mode="HTML",
        reply_markup=get_form_submit_menu("support_menu")
    )
    await state.set_state(FormStates.question_confirm)


# ===== ЖАЛОБА НА ИГРОКА =====
@router.callback_query(F.data == "support_player_complaint")
async def callback_player_complaint(callback: CallbackQuery, state: FSMContext):
    """Жалоба на игрока"""
    await callback.answer()
    await callback.message.edit_text(
        "⚠️ <b>Жалоба на игрока</b>\n\n"
        "Пожалуйста, заполните форму:\n\n"
        "<b>1. Ваш игровой ник:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.player_complaint_nickname)


@router.message(FormStates.player_complaint_nickname)
async def process_player_complaint_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer(
        "<b>2. Ник нарушителя:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.player_complaint_violator)


@router.message(FormStates.player_complaint_violator)
async def process_player_complaint_violator(message: Message, state: FSMContext):
    await state.update_data(violator=message.text)
    await message.answer(
        "<b>3. Какой пункт правил нарушил игрок:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.player_complaint_rule)


@router.message(FormStates.player_complaint_rule)
async def process_player_complaint_rule(message: Message, state: FSMContext):
    await state.update_data(rule=message.text)
    await message.answer(
        "<b>4. Доказательства в виде полного скриншота экрана, где видно игровую панель и нарушение/видео:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.player_complaint_proof)


@router.message(FormStates.player_complaint_proof)
async def process_player_complaint_proof(message: Message, state: FSMContext):
    proof_text = message.text if message.text else "[Медиа файл]"
    
    # Сохраняем медиа если есть
    media_data = {}
    if message.photo:
        media_data['type'] = 'photo'
        media_data['file_id'] = message.photo[-1].file_id
        media_data['caption'] = message.caption
    elif message.video:
        media_data['type'] = 'video'
        media_data['file_id'] = message.video.file_id
        media_data['caption'] = message.caption
    elif message.document:
        media_data['type'] = 'document'
        media_data['file_id'] = message.document.file_id
        media_data['caption'] = message.caption
    
    await state.update_data(proof=proof_text, proof_media=media_data)
    data = await state.get_data()
    
    form_text = f"""📋 <b>Проверьте вашу заявку:</b>

<b>Тип:</b> Жалоба на игрока
<b>Ваш ник:</b> {data['nickname']}
<b>Ник нарушителя:</b> {data['violator']}
<b>Нарушенный пункт правил:</b> {data['rule']}
<b>Доказательства:</b> {data['proof']}

Перепроверьте вашу заявку и нажмите на кнопку "отправить"
Если вы что-то не написали, переделайте заявку и отправьте её ещё раз."""
    
    await message.answer(
        form_text,
        parse_mode="HTML",
        reply_markup=get_form_submit_menu("support_menu")
    )
    await state.set_state(FormStates.player_complaint_confirm)


# ===== ЖАЛОБА НА АДМИНИСТРАЦИЮ =====
@router.callback_query(F.data == "support_admin_complaint")
async def callback_admin_complaint(callback: CallbackQuery, state: FSMContext):
    """Жалоба на администрацию"""
    await callback.answer()
    await callback.message.edit_text(
        "🚨 <b>Жалоба на администрацию</b>\n\n"
        "Пожалуйста, заполните форму:\n\n"
        "<b>1. Ваш игровой ник:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.admin_complaint_nickname)


@router.message(FormStates.admin_complaint_nickname)
async def process_admin_complaint_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer(
        "<b>2. Ник администратора:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.admin_complaint_admin)


@router.message(FormStates.admin_complaint_admin)
async def process_admin_complaint_admin(message: Message, state: FSMContext):
    await state.update_data(admin=message.text)
    await message.answer(
        "<b>3. Какой пункт правил нарушил администратор:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.admin_complaint_rule)


@router.message(FormStates.admin_complaint_rule)
async def process_admin_complaint_rule(message: Message, state: FSMContext):
    await state.update_data(rule=message.text)
    await message.answer(
        "<b>4. Доказательства в виде полного скриншота экрана, где видно игровую панель и нарушение/видео:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.admin_complaint_proof)


@router.message(FormStates.admin_complaint_proof)
async def process_admin_complaint_proof(message: Message, state: FSMContext):
    proof_text = message.text if message.text else "[Медиа файл]"
    
    # Сохраняем медиа если есть
    media_data = {}
    if message.photo:
        media_data['type'] = 'photo'
        media_data['file_id'] = message.photo[-1].file_id
        media_data['caption'] = message.caption
    elif message.video:
        media_data['type'] = 'video'
        media_data['file_id'] = message.video.file_id
        media_data['caption'] = message.caption
    elif message.document:
        media_data['type'] = 'document'
        media_data['file_id'] = message.document.file_id
        media_data['caption'] = message.caption
    
    await state.update_data(proof=proof_text, proof_media=media_data)
    data = await state.get_data()
    
    form_text = f"""📋 <b>Проверьте вашу заявку:</b>

<b>Тип:</b> Жалоба на администрацию
<b>Ваш ник:</b> {data['nickname']}
<b>Ник администратора:</b> {data['admin']}
<b>Нарушенный пункт правил:</b> {data['rule']}
<b>Доказательства:</b> {data['proof']}

Перепроверьте вашу заявку и нажмите на кнопку "отправить"
Если вы что-то не написали, переделайте заявку и отправьте её ещё раз."""
    
    await message.answer(
        form_text,
        parse_mode="HTML",
        reply_markup=get_form_submit_menu("support_menu")
    )
    await state.set_state(FormStates.admin_complaint_confirm)


# ===== БАГ/ДЮП =====
@router.callback_query(F.data == "support_bug")
async def callback_bug_report(callback: CallbackQuery, state: FSMContext):
    """Репорт бага/дюпа"""
    await callback.answer()
    await callback.message.edit_text(
        "🐛 <b>Нашел баг/дюп</b>\n\n"
        "Пожалуйста, заполните форму:\n\n"
        "<b>1. Ваш игровой ник:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.bug_nickname)


@router.message(FormStates.bug_nickname)
async def process_bug_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer(
        "<b>2. Максимально подробно распишите ваш вопрос в 1 сообщении:</b>",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.bug_description)


@router.message(FormStates.bug_description)
async def process_bug_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "<b>3. Предоставьте скриншот/видео, если оно есть:</b>\n"
        "(или напишите 'нет', если нет доказательств)",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.bug_proof)


@router.message(FormStates.bug_proof)
async def process_bug_proof(message: Message, state: FSMContext):
    proof_text = message.text if message.text else "[Медиа файл]"
    
    # Сохраняем медиа если есть
    media_data = {}
    if message.photo:
        media_data['type'] = 'photo'
        media_data['file_id'] = message.photo[-1].file_id
        media_data['caption'] = message.caption
    elif message.video:
        media_data['type'] = 'video'
        media_data['file_id'] = message.video.file_id
        media_data['caption'] = message.caption
    elif message.document:
        media_data['type'] = 'document'
        media_data['file_id'] = message.document.file_id
        media_data['caption'] = message.caption
    
    await state.update_data(proof=proof_text, proof_media=media_data)
    data = await state.get_data()
    
    form_text = f"""📋 <b>Проверьте вашу заявку:</b>

<b>Тип:</b> Нашел баг/дюп
<b>Ваш ник:</b> {data['nickname']}
<b>Описание:</b> {data['description']}
<b>Доказательства:</b> {data['proof']}

Перепроверьте вашу заявку и нажмите на кнопку "отправить"
Если вы что-то не написали, переделайте заявку и отправьте её ещё раз."""
    
    await message.answer(
        form_text,
        parse_mode="HTML",
        reply_markup=get_form_submit_menu("support_menu")
    )
    await state.set_state(FormStates.bug_confirm)


# ===== ДРУГОЕ =====
@router.callback_query(F.data == "support_other")
async def callback_other(callback: CallbackQuery, state: FSMContext):
    """Другое обращение"""
    await callback.answer()
    await callback.message.edit_text(
        "📝 <b>Другое</b>\n\n"
        "Опишите максимально подробно и в 1 сообщении вашу просьбу:",
        parse_mode="HTML",
        reply_markup=get_cancel_form_button()
    )
    await state.set_state(FormStates.other_text)


@router.message(FormStates.other_text)
async def process_other_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    data = await state.get_data()
    
    form_text = f"""📋 <b>Проверьте вашу заявку:</b>

<b>Тип:</b> Другое
<b>Описание:</b> {data['text']}

Перепроверьте вашу заявку и нажмите на кнопку "отправить"
Если вы что-то не написали, переделайте заявку и отправьте её ещё раз."""
    
    await message.answer(
        form_text,
        parse_mode="HTML",
        reply_markup=get_form_submit_menu("support_menu")
    )
    await state.set_state(FormStates.other_confirm)


# ===== ОБЩИЕ ОБРАБОТЧИКИ =====
@router.callback_query(F.data == "form_submit")
async def callback_form_submit(callback: CallbackQuery, state: FSMContext):
    """Отправка формы"""
    await callback.answer()
    
    current_state = await state.get_state()
    data = await state.get_data()
    
    # Определяем тип тикета
    ticket_type = None
    form_data_text = ""
    
    if current_state == FormStates.media_tiktok_confirm:
        ticket_type = "media_tiktok"
        form_data_text = f"Ник: {data['nickname']}\nКанал: {data['channel']}"
    elif current_state == FormStates.media_youtube_confirm:
        ticket_type = "media_youtube"
        form_data_text = f"Ник: {data['nickname']}\nКанал: {data['channel']}"
    elif current_state == FormStates.helper_confirm:
        ticket_type = "helper"
        form_data_text = (f"Ник: {data['nickname']}\nВозраст: {data['age']}\n"
                         f"VK: {data['vk']}\nTelegram: {data['telegram']}\nDiscord: {data['discord']}\n"
                         f"Общее время: {data['playtime']}\nВремя в вайпе: {data['wipe_playtime']}\n"
                         f"Обязанности: {data['duties']}\nОпыт: {data['experience']}")
    elif current_state == FormStates.question_confirm:
        ticket_type = "question"
        form_data_text = f"Ник: {data['nickname']}\nВопрос: {data['question']}"
    elif current_state == FormStates.player_complaint_confirm:
        ticket_type = "player_complaint"
        form_data_text = (f"Ник: {data['nickname']}\nНарушитель: {data['violator']}\n"
                         f"Пункт правил: {data['rule']}\nДоказательства: {data['proof']}")
    elif current_state == FormStates.admin_complaint_confirm:
        ticket_type = "admin_complaint"
        form_data_text = (f"Ник: {data['nickname']}\nАдмин: {data['admin']}\n"
                         f"Пункт правил: {data['rule']}\nДоказательства: {data['proof']}")
    elif current_state == FormStates.bug_confirm:
        ticket_type = "bug_report"
        form_data_text = f"Ник: {data['nickname']}\nОписание: {data['description']}\nДоказательства: {data['proof']}"
    elif current_state == FormStates.other_confirm:
        ticket_type = "other"
        form_data_text = f"Описание: {data['text']}"
    
    if not ticket_type:
        await callback.message.edit_text(
            "❌ Ошибка при отправке заявки. Попробуйте заново.",
            reply_markup=get_back_to_main()
        )
        await state.clear()
        return
    
    # Проверка на бан
    is_banned, ban_info = await db.is_user_banned(callback.from_user.id)
    if is_banned:
        import datetime
        ban_text = f"🚫 <b>Вы заблокированы и не можете создавать обращения</b>\n\n<b>Причина:</b> {ban_info['reason']}\n"
        if ban_info['is_permanent']:
            ban_text += "\n<b>Срок:</b> Навсегда"
        else:
            ban_until = datetime.datetime.fromisoformat(ban_info['ban_until'])
            ban_text += f"\n<b>До:</b> {ban_until.strftime('%d.%m.%Y %H:%M')}"
        
        await callback.message.edit_text(ban_text, parse_mode="HTML", reply_markup=get_back_to_main())
        await state.clear()
        return
    
    # Создаем тикет
    ticket_id = await db.create_ticket(
        callback.from_user.id,
        callback.from_user.username or "Unknown",
        ticket_type,
        form_data_text
    )
    
    # Сохраняем ID тикета в состоянии для дальнейшего общения
    await state.update_data(ticket_id=ticket_id)
    
    # Уведомляем администрацию
    notification_text = (
        f"📬 <b>Новое обращение #{ticket_id}</b>\n\n"
        f"<b>От:</b> @{callback.from_user.username or 'Unknown'} (ID: {callback.from_user.id})\n"
        f"<b>Тип:</b> {TICKET_TYPES.get(ticket_type, 'Неизвестно')}\n\n"
        f"<b>Данные:</b>\n{form_data_text}"
    )
    
    # Создаем кнопку для перехода к обращению
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    ticket_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Перейти к обращению", callback_data=f"view_ticket_{ticket_id}")]
    ])
    
    # Проверяем наличие медиа с доказательствами
    proof_media = data.get('proof_media', {})
    
    for admin_id in ADMIN_IDS + SUPPORT_STAFF_IDS:
        try:
            from bot import bot
            # Если есть медиа - отправляем его с caption
            if proof_media and proof_media.get('file_id'):
                media_type = proof_media.get('type')
                file_id = proof_media.get('file_id')
                
                if media_type == 'photo':
                    await bot.send_photo(admin_id, file_id, caption=notification_text, parse_mode="HTML", reply_markup=ticket_keyboard)
                elif media_type == 'video':
                    await bot.send_video(admin_id, file_id, caption=notification_text, parse_mode="HTML", reply_markup=ticket_keyboard)
                elif media_type == 'document':
                    await bot.send_document(admin_id, file_id, caption=notification_text, parse_mode="HTML", reply_markup=ticket_keyboard)
            else:
                # Если нет медиа - обычное текстовое сообщение
                await bot.send_message(admin_id, notification_text, parse_mode="HTML", reply_markup=ticket_keyboard)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    await callback.message.edit_text(
        "✅ <b>Отлично! Вы отправили заявку.</b>\n\n"
        "В скором времени мы её рассмотрим и свяжемся с вами!\n"
        "А пока можете забрать бесплатную награду на сервере.\n\n"
        "Также вы можете продолжить общение здесь - просто напишите сообщение.",
        parse_mode="HTML",
        reply_markup=get_after_submit_menu()
    )
    
    # Переводим в режим общения в тикете
    await state.set_state(FormStates.chatting_in_ticket)


@router.callback_query(F.data == "form_restart")
async def callback_form_restart(callback: CallbackQuery, state: FSMContext):
    """Перезапуск формы"""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "🔄 Форма сброшена. Выберите тип обращения заново:",
        parse_mode="HTML",
        reply_markup=get_support_menu()
    )


@router.callback_query(F.data == "cancel_form")
async def callback_cancel_form(callback: CallbackQuery, state: FSMContext):
    """Отмена заполнения формы"""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "❌ Заполнение формы отменено.",
        reply_markup=get_back_to_main()
    )


# Обработка сообщений в тикете
@router.message(FormStates.chatting_in_ticket)
async def process_ticket_message(message: Message, state: FSMContext):
    """Обработка сообщений в открытом тикете"""
    data = await state.get_data()
    ticket_id = data.get('ticket_id')
    
    if not ticket_id:
        await message.answer(
            "❌ Не найден активный тикет.",
            reply_markup=get_back_to_main()
        )
        await state.clear()
        return
    
    # Сохраняем сообщение в тикете
    await db.add_ticket_message(ticket_id, message.from_user.id, message.text or "[Медиа]")
    
    # Уведомляем администрацию
    notification_text = (
        f"💬 <b>Новое сообщение в тикете #{ticket_id}</b>\n\n"
        f"<b>От:</b> @{message.from_user.username or 'Unknown'}\n"
        f"<b>Сообщение:</b> {message.text or '[Медиа]'}"
    )
    
    for admin_id in ADMIN_IDS + SUPPORT_STAFF_IDS:
        try:
            from bot import bot
            await bot.send_message(admin_id, notification_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")
    
    await message.answer(
        "✅ Ваше сообщение отправлено администрации.",
        reply_markup=get_back_to_main()
    )

