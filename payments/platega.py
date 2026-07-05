"""Интеграция с Platega — создание платежей и проверка webhook'ов."""
import uuid
import hashlib
import logging

import aiohttp

import config

logger = logging.getLogger(__name__)


async def create_payment(
    order_id: int,
    amount: float,
    product_name: str,
    success_url: str,
    fail_url: str
) -> str:
    """
    Создать платёж через Platega.
    Возвращает URL для оплаты или пустую строку при ошибке.
    """
    try:
        # Уникальный ID транзакции
        transaction_id = str(uuid.uuid4())

        # Данные для запроса
        payload = {
            "id": transaction_id,
            "paymentMethod": 2,  # СБП/QR
            "paymentDetails": {
                "amount": int(amount * 100),  # В копейках
                "currency": "RUB"
            },
            "description": product_name,
            "return": success_url,
            "failedUrl": fail_url,
            "payload": str(order_id)
        }

        # Подпись
        sign_string = (
            f"{config.PLATEGA_MERCHANT_ID}:{transaction_id}:"
            f"{int(amount * 100)}:{config.PLATEGA_SECRET_KEY}"
        )
        signature = hashlib.sha256(sign_string.encode()).hexdigest()

        # Запрос к API
        headers = {
            "X-MerchantId": config.PLATEGA_MERCHANT_ID,
            "X-Signature": signature,
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.PLATEGA_URL}/transaction/process",
                json=payload,
                headers=headers
            ) as resp:
                data = await resp.json()

                if resp.status != 200:
                    logger.error(f"Platega: ошибка API {resp.status}: {data}")
                    return ""

                # URL для оплаты
                url = data.get("url", data.get("redirect", ""))
                if url:
                    logger.info(f"Platega: создан платёж для заказа #{order_id}")
                return url

    except Exception as e:
        logger.error(f"Platega: ошибка создания платежа: {e}")
        return ""


async def verify_webhook(data: dict) -> bool:
    """Проверка подписи webhook от Platega"""
    try:
        sign_string = (
            f"{config.PLATEGA_MERCHANT_ID}:{data.get('id', '')}:"
            f"{data.get('payload', '')}:{config.PLATEGA_SECRET_KEY}"
        )
        expected = hashlib.sha256(sign_string.encode()).hexdigest()
        return data.get("signature") == expected

    except Exception as e:
        logger.error(f"Platega: ошибка проверки подписи: {e}")
        return False
