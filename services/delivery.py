"""Автовыдача товаров"""
import os
import logging

from aiogram import Bot
from aiogram.types import FSInputFile

from database.models import Order, Product, User

logger = logging.getLogger(__name__)


async def deliver_file(order: Order, session):
    """Выдать файл после оплаты"""
    try:
        # Получаем товар
        product = await session.get(Product, order.product_id)
        if not product or not product.file_path:
            logger.error(f"Товар {order.product_id} не найден или нет файла")
            return

        # Получаем пользователя
        user = await session.get(User, order.user_id)
        if not user:
            logger.error(f"Пользователь {order.user_id} не найден")
            return

        # Проверяем существование файла
        if not os.path.exists(product.file_path):
            logger.error(f"Файл не найден: {product.file_path}")
            return

        # Отправляем файл
        from bot import bot
        file = FSInputFile(product.file_path)
        await bot.send_document(
            chat_id=user.telegram_id,
            document=file,
            caption=f"✅ Оплата получена!\n\n"
                   f"📦 Товар: {product.name}\n"
                   f"💰 Сумма: {order.amount} ₽\n\n"
                   "Спасибо за покупку! 🎉"
        )

        # Обновляем статус
        order.status = "delivered"
        await session.commit()

        logger.info(f"Товар {product.name} выдан пользователю {user.telegram_id}")

    except Exception as e:
        logger.error(f"Ошибка выдачи файла: {e}")
