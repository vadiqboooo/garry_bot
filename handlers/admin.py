from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from database import get_all_user, get_new_user,  get_phone_user

admin = Router()

LIST_ADMIN = [431589340, 43961092]

admin.message.filter((F.from_user.id.in_(LIST_ADMIN)))

async def send_alert(message: Message, contact = None):
    ADMIN_ID = LIST_ADMIN[0]

    if contact == None:
        message_text =  f"✅ Зашел новый пользователь!\n"
        message_text += f"Имя пользователя: @{message.from_user.username}\n"
        message_text += f"User ID: {message.from_user.id}"
    else:
        message_text =  f"✅ Контакт получен!\n"
        message_text += f"Имя: {contact.first_name}\n"
        message_text += f"Телефон: {contact.phone_number}\n"
        message_text += f"User ID: {contact.user_id}"
    
    for admin in LIST_ADMIN:
        await message.bot.send_message(chat_id = admin, 
                                   text=message_text)

class msg_state(StatesGroup):
    text = State()
    mailing_type = State()

@admin.message(Command('admin'))
async def admin_msg(message: Message):

    text = '''⚙️ *АДМИН-ПАНЕЛЬ* ⚙️
───────────────────

📤 Рассылка сообщений:

1. 📢 /send_all - Всем пользователям
2. 🆕 /send_new - Новым (без телефона)
3. 📞 /send_phone - Только с телефонами'''

    await message.answer(text)


@admin.message(Command('send_all'))
async def admin_send_all(message: Message, state: FSMContext):
    await state.update_data(mailing_type = 'all')
    await message.answer('Введите текст, который хотите отправить всем:')
    await state.set_state(msg_state.text)
    

@admin.message(Command('send_new'))
async def admin_send_new(message: Message, state: FSMContext):
    await state.update_data(mailing_type = 'new')
    await message.answer('Введите текст, который хотите отправить, тем кто не указал свой телефон:')
    await state.set_state(msg_state.text)


@admin.message(Command('send_phone'))
async def admin_send_phone(message: Message, state: FSMContext):
    await state.update_data(mailing_type = 'phone')
    await message.answer('Введите текст, который хотите отправить только тем кто указал телефон:')
    await state.set_state(msg_state.text)


@admin.message(msg_state.text)
async def send_message(message: Message, state: FSMContext):
    data = await state.get_data()  # Получаем сохраненный тип рассылки
    mailing_type = data.get("mailing_type")
    text_to_send = message.text

    if mailing_type == 'all':
        users = await get_all_user()
    elif mailing_type == 'new':
        users = await get_new_user()
    elif mailing_type == 'phone':
        users = await get_phone_user()

    else:
        await message.answer("❌ Ошибка: неизвестный тип рассылки, обратитесь к @rancheasy")
        return

    user_ids = 0
    for user in users:
        try:
            await message.bot.send_message(chat_id=user.telegram_id,
                                       text = text_to_send)
            user_ids += 1
        except:
            ...
        
    await message.answer(f"✅ Рассылка завершена! Получателей: {user_ids}")
    await state.clear()