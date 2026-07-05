"""Интеграция с Prodamus"""
import hashlib
import hmac
import uuid
from urllib.parse import urlencode

import aiohttp

import config


async def create_payment(
    order_id: int,
    amount: float,
    product_name: str,
    success_url: str,
    fail_url: str
) -> str:
    """
    Создать платёж через Prodamus
    Возвращает URL для оплаты
    """
    # Формируем данные
    data = {
        "shopId": config.PRODAMUS_SHOP_ID,
        "sum": amount,
        "orderNumber": str(order_id),
        "productName": product_name,
        "successUrl": success_url,
        "failUrl": fail_url,
    }

    # Подпись HMAC
    sign_string = "&".join(f"{k}={v}" for k, v in sorted(data.items()))
    signature = hmac.new(
        config.PRODAMUS_SECRET_KEY.encode(),
        sign_string.encode(),
        hashlib.sha256
    ).hexdigest()

    # Формируем URL
    params = urlencode({**data, "signature": signature})
    payment_url = f"{config.PRODAMUS_URL}/pay?{params}"

    return payment_url


async def verify_webhook(data: dict, signature: str) -> bool:
    """Проверка подписи webhook от Prodamus"""
    # Сортируем данные (кроме signature)
    sign_data = {k: v for k, v in sorted(data.items()) if k != "signature"}
    sign_string = "&".join(f"{k}={v}" for k, v in sign_data.items())

    expected = hmac.new(
        config.PRODAMUS_SECRET_KEY.encode(),
        sign_string.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)
