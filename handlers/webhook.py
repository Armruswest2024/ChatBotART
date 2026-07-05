"""Webhook-хендлеры для платёжных систем (чистый aiohttp).

Это НЕ aiogram-роутер — здесь обрабатываются HTTP-запросы от
Prodamus и Platega при подтверждении оплаты.
"""
import logging
from datetime import datetime

from aiohttp import web

from database.db import async_session
from database.models import Order
from services.delivery import deliver_file

logger = logging.getLogger(__name__)


async def handle_prodamus_webhook(request: web.Request) -> web.Response:
    """Webhook от Prodamus — вызывается при оплате"""
    from payments.prodamus import verify_webhook

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    signature = request.headers.get("X-Signature", "")

    # Проверяем подпись
    if not await verify_webhook(data, signature):
        logger.warning("Prodamus: неверная подпись webhook")
        return web.json_response({"error": "Invalid signature"}, status=400)

    # Получаем ID заказа и статус
    order_id = data.get("orderNumber")
    status = data.get("status")

    logger.info(f"Prodamus webhook: заказ #{order_id}, статус={status}")

    if status == "paid":
        await _confirm_payment(order_id, "prodamus")

    return web.json_response({"ok": True})


async def handle_platega_webhook(request: web.Request) -> web.Response:
    """Webhook от Platega — вызывается при оплате"""
    from payments.platega import verify_webhook

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    # Проверяем подпись
    if not await verify_webhook(data):
        logger.warning("Platega: неверная подпись webhook")
        return web.json_response({"error": "Invalid signature"}, status=400)

    # Получаем ID заказа и статус
    order_id = data.get("payload")
    status = data.get("status")

    logger.info(f"Platega webhook: заказ #{order_id}, статус={status}")

    if status == "success":
        await _confirm_payment(order_id, "platega")

    return web.json_response({"ok": True})


async def _confirm_payment(order_id, payment_system: str):
    """Подтверждение оплаты и выдача товара"""
    try:
        async with async_session() as session:
            order = await session.get(Order, int(order_id))
            if order and order.status == "pending":
                order.status = "paid"
                order.paid_at = datetime.utcnow()
                await session.commit()

                # Выдаём товар
                await deliver_file(order, session)

                logger.info(f"Заказ #{order_id} оплачен ({payment_system})")
            elif order:
                logger.warning(f"Заказ #{order_id} уже в статусе {order.status}")
            else:
                logger.error(f"Заказ #{order_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка подтверждения оплаты: {e}")


def register_webhook_routes(app: web.Application):
    """Регистрация маршрут webhook'ов на aiohttp-приложении"""
    app.router.add_post("/webhook/prodamus", handle_prodamus_webhook)
    app.router.add_post("/webhook/platega", handle_platega_webhook)
    logger.info("Webhook-маршруты зарегистрированы: /webhook/prodamus, /webhook/platega")
