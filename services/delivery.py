"""Автовыдача товаров после оплаты"""
import os
import logging

from aiogram.types import FSInputFile

from core import bot
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
        file = FSInputFile(product.file_path)
        await bot.send_document(
            chat_id=user.telegram_id,
            document=file,
            caption=(
                f"✅ Оплата получена!\n\n"
                f"📦 Товар: {product.name}\n"
                f"💰 Сумма: {order.amount} ₽\n\n"
                "Спасибо за покупку! 🎉"
            )
        )

        # Обновляем статус
        order.status = "delivered"
        await session.commit()

        logger.info(f"Товар {product.name} выдан пользователю {user.telegram_id}")

    except Exception as e:
        logger.error(f"Ошибка выдачи файла: {e}")


async def send_payment_error(chat_id: int, order_id: int):
    """Уведомление об ошибке оплаты"""
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"❌ Ошибка при создании оплаты (заказ #{order_id})\n\n"
                "Попробуйте ещё раз или выберите другой способ оплаты."
            )
        )
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")
