from sqlalchemy import select, Column, Integer, String, BigInteger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Optional

# Конфигурация базы данных (aiosqlite)
DATABASE_URL = "sqlite+aiosqlite:///bot_database.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

# Модель пользователя
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String(100), nullable=True)
    phone_number = Column(String(20), nullable=True)


class Admin(Base):
    __tablename__ = 'admins'

    telegram_id = Column(BigInteger, unique=True, primary_key=True)
    role = Column(Integer, nullable=True)


# ====== Хэндлеры и функции ====== #
async def init_db():
    """Создание таблиц в БД"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    

async def add_admin(telegram_id: int):
    async with async_session() as session:
        try:
            new_admin = Admin(telegram_id = telegram_id)
            session.add(new_admin)
            await session.commit()
            return True
        except: 
            return False

async def delete_admin(telegram_id: int):
    async with async_session() as session:
        admin = await session.scalar(select(Admin).where(Admin.telegram_id == telegram_id))
        if admin:
            await session.delete(admin)
            await session.commit()
            return True
        else:
            return False
        
async def get_admin_ids():
    """Получаем ID администраторов из базы данных"""
    async with async_session() as session:
        result = await session.execute(
            select(Admin.telegram_id)
        )
        return [row[0] for row in result.all()]

async def get_admin():
    async with async_session() as session:
        admins = await session.scalars(select(Admin))
        return admins.all()

async def add_user(telegram_id: int, username: Optional[str] = None, phone_number: Optional[str] = None):
    """Добавление пользователя в БД"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if not user:
            new_user = User(telegram_id=telegram_id, username=username, phone_number=phone_number)
            session.add(new_user)
            await session.commit()
            return True
        else:
            return False

async def update_user(telegram_id: int, phone_number: Optional[str] = None):
    """Добавление пользователю номер телефона"""
    async with async_session() as session:
        
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user:
            user.phone_number = phone_number
        await session.commit()


async def delete_user(telegram_id: int):
    """Добавление пользователю номер телефона"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if user:
            await session.delete(user)
            await session.commit()
            return True
        else:
            return False



async def get_user(telegram_id: int) -> Optional[User]:
    """Получение пользователя из БД"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))

        return user

async def get_all_user() -> Optional[User]:
    """Получение пользователя из БД"""
    async with async_session() as session:
        result = await session.scalars(select(User))

        return result.all()


async def get_new_user() -> Optional[User]:
    """Получение пользователя из БД"""
    async with async_session() as session:
        result = await session.scalars(select(User).where(User.phone_number == ''))

        return result.all() 

async def get_phone_user() -> Optional[User]:
    """Получение пользователя из БД"""
    async with async_session() as session:
        result = await session.scalars(select(User).where(User.phone_number != ''))

        return result.all()       
