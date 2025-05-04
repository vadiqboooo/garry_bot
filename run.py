import asyncio

from aiogram import Bot, Dispatcher
from database import init_db

from handlers.admin import admin
from handlers.user import user, scheduler
from config import TELEGRAM_TOKEN, TEST_TOKEN

# Настройка логирования
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN)  # Замените на свой токен!
dp = Dispatcher()


# ====== Запуск бота ====== #
async def main():
    await init_db()  # Создаем таблицы при старте
    dp.include_router(user)
    dp.include_router(admin)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())