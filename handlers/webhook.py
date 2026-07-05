"""Webhook handlers для платёжных систем"""
from datetime import datetime

from aiogram import Router, F
from aiohttp import web

from database.db import get_session
from database.models import Order
from services.delivery import deliver_file

router = Router()


async def handle_prodamus_webhook(request: web.Request) -> web.Response:
    """Webhook от Prodamus"""
    from payments.prodamus import verify_webhook

    data = await request.json()
    signature = request.headers.get("X-Signature", "")

    # Проверяем подпись
    if not await verify_webhook(data, signature):
        return web.json_response({"error": "Invalid signature"}, status=400)

    # Получаем ID заказа
    order_id = data.get("orderNumber")
    status = data.get("status")

    if status == "paid":
        await confirm_payment(order_id, "prodamus")

    return web.json_response({"ok": True})


async def handle_platega_webhook(request: web.Request) -> web.Response:
    """Webhook от Platega"""
    from payments.platega import verify_webhook

    data = await request.json()

    # Проверяем подпись
    if not await verify_webhook(data):
        return web.json_response({"error": "Invalid signature"}, status=400)

    # Получаем ID заказа
    order_id = data.get("payload")
    status = data.get("status")

    if status == "success":
        await confirm_payment(order_id, "platega")

    return web.json_response({"ok": True})


async def confirm_payment(order_id: int, payment_system: str):
    """Подтверждение оплаты"""
    session = await get_session()
    try:
        order = await session.get(Order, int(order_id))
        if order and order.status == "pending":
            order.status = "paid"
            order.paid_at = datetime.utcnow()
            await session.commit()

            # Выдаём товар
            await deliver_file(order, session)
    finally:
        await session.close()
