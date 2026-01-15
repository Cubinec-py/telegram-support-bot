import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.database.repositories import TicketRepository
from bot.database.models import TicketStatus
from bot.utils.notifications import notify_user_ticket_auto_closed

logger = logging.getLogger(__name__)


async def check_and_close_inactive_tickets(session_maker: async_sessionmaker, bot: Bot):
    """Check and close tickets without user response for more than 1 hour"""
    try:
        async with session_maker() as session:
            ticket_repo = TicketRepository(session)

            # Get all tickets waiting for user response
            tickets_to_check = await ticket_repo.get_tickets_waiting_user()

            now = datetime.utcnow()
            closed_count = 0

            for ticket in tickets_to_check:
                # Check if last update was more than 1 hour ago
                time_diff = now - ticket.updated_at

                if time_diff > timedelta(hours=1):
                    # Close ticket
                    await ticket_repo.close_ticket(ticket.id)

                    # Notify user
                    try:
                        await notify_user_ticket_auto_closed(
                            bot,
                            ticket.user.telegram_id,
                            ticket.ticket_number,
                            ticket.user.language
                        )
                        closed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to notify user {ticket.user.telegram_id}: {e}")

            if closed_count > 0:
                logger.info(f"Auto-closed {closed_count} inactive tickets")

    except Exception as e:
        logger.error(f"Error in check_and_close_inactive_tickets: {e}")


async def start_ticket_auto_close_scheduler(session_maker: async_sessionmaker, bot: Bot):
    """Start scheduler to check inactive tickets every 5 minutes"""
    logger.info("Starting ticket auto-close scheduler")

    while True:
        try:
            await check_and_close_inactive_tickets(session_maker, bot)
            # Check every 5 minutes
            await asyncio.sleep(300)
        except asyncio.CancelledError:
            logger.info("Ticket auto-close scheduler stopped")
            break
        except Exception as e:
            logger.error(f"Error in scheduler: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retry

