from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, BaseFilter, CommandObject
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from aiogram.enums import ParseMode

from database import *

admin = Router()



class DynamicAdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        admin_ids = await get_admin_ids()  # Ваша функция получения админов
        return message.from_user.id in admin_ids
# LIST_ADMIN = [431589340] #4396    10902
LIST_ADMIN = DynamicAdminFilter()

admin.message.filter(LIST_ADMIN)

async def send_alert(message: Message, contact = None):
    # ADMIN_ID = LIST_ADMIN[0]

    if contact == None:
        message_text =  f"✅ Зашел новый пользователь!\n"
        message_text += f"Имя пользователя: @{message.from_user.username}\n"
        message_text += f"User ID: {message.from_user.id}"
    else:
        message_text =  f"✅ Контакт получен!\n"
        message_text += f"Имя: {contact.first_name}\n"
        message_text += f"Телефон: {contact.phone_number}\n"
        message_text += f"User ID: {contact.user_id}"
    
    for admin in await get_admin_ids():
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
3. 📞 /send_phone - Только с телефонами

📋 Действия с пользователями

1. 📁 /users - показать список всех

👨‍🚀 Действия с администраторами

1. /new_admin <ID> - добавляет нового админа, указываем его ID
2. /delete_admin <ID> - удалить админа, указываем его ID
3. /get_admin - получить список всех админов

'''

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
    text_to_send = message.md_text

    photo_file_id  = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id

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
            if photo_file_id == None:
                await message.bot.send_message(chat_id=user.telegram_id,
                                        text = text_to_send,
                                        parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await message.bot.send_photo(chat_id=user.telegram_id,
                                        photo=photo_file_id,
                                        caption = text_to_send,
                                        parse_mode=ParseMode.MARKDOWN_V2)
            user_ids += 1
        except:
            ...
        
    await message.answer(f"✅ Рассылка завершена! Получателей: {user_ids}")
    await state.clear()


class DELETE_USER(StatesGroup):
    telegram_id = State()

@admin.message(Command('new_admin'))
async def admin_send_new(message: Message, command: CommandObject):
    user_id = command.args
    if await add_admin(int(user_id)):
        await message.answer(f'Новый админ успешно добавлен')
    else:
        await message.answer(f'Упс, не получилось добавить')
    
@admin.message(Command('delete_admin'))
async def admin_send_new(message: Message, command: CommandObject):
    user_id = command.args
    if await delete_admin(int(user_id)):
        await message.answer(f'Админ удален')
    else:
        await message.answer(f'Такого админа нет')

@admin.message(Command('get_admin'))
async def admin_send_new(message: Message):
    admins = await get_admin()
    text = 'Список ID админов:\n'
    for i, admin in enumerate(admins):
        text += f'{i + 1}. ID: {admin.telegram_id}\n'
    
    await message.answer(text)


@admin.message(Command('delete_user'))
async def admin_send_new(message: Message, state: FSMContext):
    await message.answer('Введите ID пользователя:')
    await state.set_state(DELETE_USER.telegram_id)

@admin.message(DELETE_USER.telegram_id)
async def cmd_delete_user(message: Message, state: FSMContext):
    id_user = message.text
    if await delete_user(id_user):
        await message.answer('Пользователь удален')
    else:
        await message.answer('Такого пользователя нет')

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def users_list_keyboard(page: int = 0, users_per_page: int = 5):
    users = await get_all_user()
    total_pages = (len(users) + users_per_page - 1) // users_per_page
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Кнопки пользователей на текущей странице
    for user in users[page*users_per_page : (page+1)*users_per_page]:
        text_admin = ''
        if user.telegram_id in await get_admin_ids():
            text_admin = "(admin)"
        keyboard.inline_keyboard.append([  # Добавляем кнопки вручную
            InlineKeyboardButton(
                text=f"👤{text_admin} {user.username}",
                callback_data=f"user_detail_{user.telegram_id}"
            )
        ])
    
    # Пагинация
    if len(users) > users_per_page:
        row = []
        if page > 0:
            row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"users_page_{page-1}"))
        if page < (len(users) // users_per_page):
            row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"users_page_{page+1}"))
        
        keyboard.inline_keyboard.append(row)
    
    return keyboard
    


@admin.message(Command('users'))
async def cmd_users(message: Message):
    
    await message.answer(
        "📋 Список пользователей:",
        reply_markup=await users_list_keyboard()
    )

@admin.callback_query(lambda c: c.data.startswith('users_page_'))
async def users_page_callback(callback: CallbackQuery):
    page = int(callback.data.split('_')[-1])
    await callback.message.edit_text(text="📋 Список пользователей:",
        reply_markup=await users_list_keyboard(page)
    )

@admin.callback_query(lambda c: c.data.startswith('user_detail_'))
async def user_detail_callback(callback: CallbackQuery):
    telegram_id = int(callback.data.split('_')[-1])
    user = await get_user(telegram_id)
    
    if not user:
        return await callback.answer("Пользователь не найден!")
    
    text = (
        f"👤 Информация о пользователе\n"
        f"├ ID: {user.telegram_id}\n"
        f"├ Юзернейм: @{user.username or '❌'}\n"
        f"├ Телефон: {user.phone_number or '❌'}\n"
    )

    # Создаем клавиатуру с кнопкой "Удалить"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="✉️ Написать",
            callback_data=f"pm_user_{user.telegram_id}"
        )
    ],
    [
        InlineKeyboardButton(
            text="🗑️ Удалить",
            callback_data=f"delete_user_{user.telegram_id}"
        )
    ],
    [
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="users_page_0"
        )
    ]
])
    
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@admin.callback_query(lambda c: c.data.startswith('delete_user_'))
async def delete_user_callback(callback: CallbackQuery):
    telegram_id = int(callback.data.split('_')[-1])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_delete_{telegram_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel_delete")
        ]
    ])
    await callback.message.edit_text("Вы уверены, что хотите удалить пользователя?", reply_markup=keyboard)

@admin.callback_query(lambda c: c.data.startswith('confirm_delete_'))
async def confirm_delete_callback(callback: CallbackQuery):
    telegram_id = int(callback.data.split('_')[-1])
    await delete_user(telegram_id)
    await callback.message.edit_text("✅ Пользователь удален!", reply_markup=None)

@admin.callback_query(lambda c: c.data == "cancel_delete")
async def cancel_delete_callback(callback: CallbackQuery):
    await callback.message.edit_text("❌ Удаление отменено.", reply_markup=None)

class PMStates(StatesGroup):
    waiting_for_message = State()

@admin.callback_query(lambda c: c.data.startswith('pm_user_'))
async def start_pm_to_user(callback: CallbackQuery, state: FSMContext):
    telegram_id = int(callback.data.split('_')[-1])
    
    # Сохраняем ID пользователя в FSM
    await state.update_data(target_user_id=telegram_id)
    
    # Запрашиваем текст сообщения
    await callback.message.answer(
        "📝 Введите сообщение для пользователя:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_pm")]
        ])
    )
    await state.set_state(PMStates.waiting_for_message)
    await callback.answer()

@admin.message(PMStates.waiting_for_message)
async def process_pm_message(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data['target_user_id']
    
    try:
        # Пытаемся отправить сообщение
        await message.bot.send_message(
            chat_id=target_user_id,
            text=f"📨 Сообщение от администратора:\n\n{message.text}"
        )
        await message.answer("✅ Сообщение успешно отправлено!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    
    await state.clear()

@admin.callback_query(lambda c: c.data == "cancel_pm")
async def cancel_pm(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Отправка отменена")
    await callback.answer()