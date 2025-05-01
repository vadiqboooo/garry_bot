from aiogram import Router
from time import sleep
from datetime import *

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from database import add_user, update_user, get_user, add_admin

from message_file import text
from handlers.admin import send_alert

user = Router()
scheduler = AsyncIOScheduler()


# ====== Команды ====== #
@user.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка /start"""
    await add_admin(431589340)
    print('админ добавлен')
    user = message.from_user
    
    # Добавляем пользователя в БД
    new_user = await add_user(telegram_id=user.id, username=user.username, phone_number=None)

    
    get_contact_kb = ReplyKeyboardMarkup(
                    keyboard=[
                        [KeyboardButton(text="📱 Отправить контакт", request_contact=True)]
                    ],
                    resize_keyboard=True,  # Подгоняет размер клавиатуры
                    one_time_keyboard=True  # Скрывает клавиатуру после нажатия
                )
    
    if new_user:
        await send_alert(message=message)
        await message.answer(text['welcome'])
        sleep(3)
        await message.answer(text['about'], reply_markup=get_contact_kb)
    else:
        user = await get_user(telegram_id=user.id)
        if user.phone_number == '':
            await message.answer(text=text['not_phone'], reply_markup=get_contact_kb)
        else:
            await message.answer(text=text['timing'])


@user.message(lambda message: message.contact is not None)
async def handle_contact(message: Message):
    """Обработка полученного контакта"""
    contact = message.contact
    await update_user(telegram_id=contact.user_id, phone_number=contact.phone_number)
    await message.answer(
        text = text['finaly'],
        reply_markup=ReplyKeyboardRemove()  # Убираем клавиатуру
    )
    await send_alert(message=message, contact=contact)

    # Планируем уведомление
    scheduler.add_job(
        send_notification,
        'date',
        run_date=datetime.now() + timedelta(hours=2),
        args=[message.bot, message.chat.id]
    )

async def send_notification(bot, chat_id: int):

    text_notif = '''✨ Не забудь позвать друзей! ✨

🚀 Отправь им ссылку на нашего бота – и прокачайте первую часть вместе!
🔥 Вместе веселее, а достижения – круче!

👉 @garry_school_bot'''
    await bot.send_message(chat_id, 
                           text=text_notif)
