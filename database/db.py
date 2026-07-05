"""Настройки БД — движок, сессии, инициализация таблиц."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

import config

# Движок (async SQLite по умолчанию)
engine = create_async_engine(config.DATABASE_URL, echo=False)

# Фабрика сессий
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Базовый класс для моделей"""
    pass


async def init_db():
    """Создание таблиц (если ещё не существуют)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
