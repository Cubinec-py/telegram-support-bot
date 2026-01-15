import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from bot.utils.i18n import i18n

logger = logging.getLogger(__name__)


async def notify_manager_new_ticket(bot: Bot, manager_telegram_id: int, ticket, user, message_text: str):
    """Notify manager about new ticket"""
    try:
        notification = i18n.get(
            "manager.new_ticket_notification",
            "ru",
            ticket_number=ticket.ticket_number,
            user_name=user.first_name or f"User {user.telegram_id}",
            message=message_text[:200]
        )
        await bot.send_message(manager_telegram_id, notification)
    except Exception as e:
        logger.error(f"Failed to notify manager {manager_telegram_id}: {e}")


async def notify_manager_new_message(bot: Bot, manager_telegram_id: int, ticket, message_text: str):
    """Notify manager about new message in ticket"""
    try:
        notification = f"💬 Новое сообщение в тикете {ticket.ticket_number}:\n\n{message_text[:200]}"
        await bot.send_message(manager_telegram_id, notification)
    except Exception as e:
        logger.error(f"Failed to notify manager {manager_telegram_id}: {e}")


async def notify_user_manager_assigned(bot: Bot, user_telegram_id: int, ticket_number: str, manager_name: str, language: str):
    """Notify user that manager was assigned"""
    try:
        notification = i18n.get(
            "tickets.manager_assigned",
            language,
            manager_name=manager_name
        )
        await bot.send_message(user_telegram_id, notification)
    except Exception as e:
        logger.error(f"Failed to notify user {user_telegram_id}: {e}")


async def notify_user_ticket_closed(bot: Bot, user_telegram_id: int, ticket_number: str, language: str):
    """Notify user that ticket was closed"""
    try:
        notification = i18n.get(
            "tickets.closed",
            language,
            ticket_number=ticket_number
        )
        await bot.send_message(user_telegram_id, notification)
    except Exception as e:
        logger.error(f"Failed to notify user {user_telegram_id}: {e}")


async def notify_user_ticket_auto_closed(bot: Bot, user_telegram_id: int, ticket_number: str, language: str):
    """Notify user that ticket was auto-closed due to inactivity"""
    try:
        notification = i18n.get(
            "tickets.auto_closed",
            language,
            ticket_number=ticket_number
        )
        await bot.send_message(user_telegram_id, notification)
    except Exception as e:
        logger.error(f"Failed to notify user {user_telegram_id}: {e}")


async def send_message_to_user(bot: Bot, user_telegram_id: int, ticket_number: str, message_text: str, language: str):
    """Send message from manager to user"""
    try:
        notification = i18n.get(
            "tickets.new_message",
            language,
            ticket_number=ticket_number,
            message=message_text
        )
        await bot.send_message(user_telegram_id, notification)
    except Exception as e:
        logger.error(f"Failed to send message to user {user_telegram_id}: {e}")

