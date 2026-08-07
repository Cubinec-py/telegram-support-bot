import logging
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError

from bot.utils.i18n import i18n

logger = logging.getLogger(__name__)


def message_preview(message_text: Optional[str], language: str) -> str:
    """Text to embed in a notification for a message that might be a sticker"""
    if message_text:
        return message_text[:200]
    return i18n.get("tickets.sticker_label", language)


async def _safe_send(bot: Bot, chat_id: int, text: str, sticker_file_id: Optional[str] = None) -> None:
    """Send a notification (and, if present, the sticker it's about right
    after), treating a blocked bot / deactivated chat as an expected outcome
    (logged at info level) rather than an error worth alarming on — as
    opposed to other Telegram API failures, which are real problems."""
    try:
        await bot.send_message(chat_id, text)
        if sticker_file_id:
            await bot.send_sticker(chat_id, sticker_file_id)
    except TelegramForbiddenError:
        logger.info(f"Chat {chat_id} is unreachable (bot blocked or user/manager deactivated)")
    except TelegramAPIError as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")


async def notify_manager_new_ticket(bot: Bot, manager_telegram_id: int, ticket, user, message_text: Optional[str], language: str = "ru", sticker_file_id: Optional[str] = None):
    """Notify manager about new ticket"""
    notification = i18n.get(
        "manager.new_ticket_notification",
        language,
        ticket_number=ticket.ticket_number,
        user_name=user.first_name or f"User {user.telegram_id}",
        message=message_preview(message_text, language)
    )
    await _safe_send(bot, manager_telegram_id, notification, sticker_file_id)


async def notify_manager_new_message(bot: Bot, manager_telegram_id: int, ticket, message_text: Optional[str], language: str = "ru", sticker_file_id: Optional[str] = None):
    """Notify manager about new message in ticket"""
    notification = i18n.get(
        "manager.new_message_notification",
        language,
        ticket_number=ticket.ticket_number,
        message=message_preview(message_text, language)
    )
    await _safe_send(bot, manager_telegram_id, notification, sticker_file_id)


async def notify_user_manager_assigned(bot: Bot, user_telegram_id: int, ticket_number: str, manager_name: str, language: str):
    """Notify user that manager was assigned"""
    notification = i18n.get(
        "tickets.manager_assigned",
        language,
        manager_name=manager_name
    )
    await _safe_send(bot, user_telegram_id, notification)


async def notify_user_ticket_closed(bot: Bot, user_telegram_id: int, ticket_number: str, language: str):
    """Notify user that ticket was closed"""
    notification = i18n.get(
        "tickets.closed",
        language,
        ticket_number=ticket_number
    )
    await _safe_send(bot, user_telegram_id, notification)


async def notify_user_ticket_auto_closed(bot: Bot, user_telegram_id: int, ticket_number: str, language: str):
    """Notify user that ticket was auto-closed due to inactivity"""
    notification = i18n.get(
        "tickets.auto_closed",
        language,
        ticket_number=ticket_number
    )
    await _safe_send(bot, user_telegram_id, notification)


async def send_message_to_user(bot: Bot, user_telegram_id: int, ticket_number: str, message_text: Optional[str], language: str, sticker_file_id: Optional[str] = None):
    """Send message from manager to user"""
    notification = i18n.get(
        "tickets.new_message",
        language,
        ticket_number=ticket_number,
        message=message_preview(message_text, language)
    )
    await _safe_send(bot, user_telegram_id, notification, sticker_file_id)
