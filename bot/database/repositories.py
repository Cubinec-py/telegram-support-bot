from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import User, Manager, Ticket, Message, TicketStatus, ManagerStatus


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, telegram_id: int, username: Optional[str] = None,
                           first_name: Optional[str] = None, last_name: Optional[str] = None,
                           language: str = "ru") -> User:
        """Get existing user or create new one"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language=language
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        else:
            # Update user info
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.updated_at = datetime.utcnow()
            await self.session.commit()

        return user

    async def update_language(self, telegram_id: int, language: str) -> Optional[User]:
        """Update user language"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.language = language
            user.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


class ManagerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, telegram_id: int, username: Optional[str] = None,
                           first_name: str = "") -> Manager:
        """Get existing manager or create new one"""
        result = await self.session.execute(
            select(Manager).where(Manager.telegram_id == telegram_id)
        )
        manager = result.scalar_one_or_none()

        if not manager:
            manager = Manager(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                status=ManagerStatus.ONLINE
            )
            self.session.add(manager)
            await self.session.commit()
            await self.session.refresh(manager)

        return manager

    async def update_status(self, telegram_id: int, status: ManagerStatus) -> Optional[Manager]:
        """Update manager status"""
        result = await self.session.execute(
            select(Manager).where(Manager.telegram_id == telegram_id)
        )
        manager = result.scalar_one_or_none()

        if manager:
            manager.status = status
            manager.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(manager)

        return manager

class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, subject: Optional[str] = None) -> Ticket:
        """Create new ticket"""
        # Generate ticket number
        result = await self.session.execute(
            select(func.count(Ticket.id))
        )
        count = result.scalar() or 0
        ticket_number = f"TKT-{count + 1:06d}"

        ticket = Ticket(
            ticket_number=ticket_number,
            user_id=user_id,
            subject=subject,
            status=TicketStatus.OPEN
        )
        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)

        return ticket

    async def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Get ticket by ID with relationships"""
        result = await self.session.execute(
            select(Ticket)
            .options(selectinload(Ticket.user), selectinload(Ticket.manager))
            .where(Ticket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def get_by_number(self, ticket_number: str) -> Optional[Ticket]:
        """Get ticket by number"""
        result = await self.session.execute(
            select(Ticket)
            .options(selectinload(Ticket.user), selectinload(Ticket.manager))
            .where(Ticket.ticket_number == ticket_number)
        )
        return result.scalar_one_or_none()

    async def get_user_active_tickets(self, user_id: int) -> List[Ticket]:
        """Get all active tickets for user"""
        result = await self.session.execute(
            select(Ticket)
            .where(
                and_(
                    Ticket.user_id == user_id,
                    Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_USER])
                )
            )
            .order_by(Ticket.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_manager_active_tickets(self, manager_id: int) -> List[Ticket]:
        """Get all active tickets for manager"""
        result = await self.session.execute(
            select(Ticket)
            .options(selectinload(Ticket.user))
            .where(
                and_(
                    Ticket.manager_id == manager_id,
                    Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_USER])
                )
            )
            .order_by(Ticket.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_unassigned_tickets(self) -> List[Ticket]:
        """Get all unassigned tickets"""
        result = await self.session.execute(
            select(Ticket)
            .options(selectinload(Ticket.user))
            .where(
                and_(
                    Ticket.manager_id.is_(None),
                    Ticket.status == TicketStatus.OPEN
                )
            )
            .order_by(Ticket.created_at)
        )
        return list(result.scalars().all())

    async def assign_manager(self, ticket_id: int, manager_id: int) -> Optional[Ticket]:
        """
        Assign a manager to an unassigned OPEN ticket.

        Locks the ticket row first and re-checks its state under the lock, so two
        concurrent assignment attempts (e.g. a manager double-tapping "take" or
        auto-assign racing a manual claim) can't both succeed: the loser sees the
        ticket already assigned/closed and gets None back instead of overwriting
        the winner's assignment or sending a duplicate notification.
        """
        result = await self.session.execute(
            select(Ticket).where(Ticket.id == ticket_id).with_for_update()
        )
        ticket = result.scalar_one_or_none()
        if not ticket or ticket.status != TicketStatus.OPEN or ticket.manager_id is not None:
            return None

        ticket.manager_id = manager_id
        ticket.status = TicketStatus.IN_PROGRESS
        ticket.updated_at = datetime.utcnow()
        await self.session.commit()
        return await self.get_by_id(ticket_id)

    async def claim_if_unassigned(self, ticket_id: int, manager_id: int) -> Optional[Ticket]:
        """
        Assign a manager to a ticket that has no manager yet, regardless of
        status — covers a manager replying directly instead of using "Взять
        в работу" first. Without this, replying doesn't set manager_id, so
        the ticket falls out of the unassigned queue (status moves off OPEN)
        without ever landing in that manager's "my tickets" either — it's
        simply orphaned. Locked the same way as assign_manager to avoid two
        managers racing to claim the same ticket via simultaneous replies.
        """
        result = await self.session.execute(
            select(Ticket).where(Ticket.id == ticket_id).with_for_update()
        )
        ticket = result.scalar_one_or_none()
        if not ticket or ticket.manager_id is not None:
            return None

        ticket.manager_id = manager_id
        ticket.updated_at = datetime.utcnow()
        await self.session.commit()
        return await self.get_by_id(ticket_id)

    async def update_status(self, ticket_id: int, status: TicketStatus) -> Optional[Ticket]:
        """
        Update ticket status.

        Locks the row and no-ops if the ticket is already in the target status,
        so two concurrent closers (two managers, or a manager racing the
        auto-close scheduler) can't both "succeed" and each fire off a duplicate
        notification to the user.
        """
        result = await self.session.execute(
            select(Ticket).where(Ticket.id == ticket_id).with_for_update()
        )
        ticket = result.scalar_one_or_none()
        if not ticket or ticket.status == status:
            return None

        ticket.status = status
        ticket.updated_at = datetime.utcnow()
        if status == TicketStatus.CLOSED:
            ticket.closed_at = datetime.utcnow()
        await self.session.commit()
        return await self.get_by_id(ticket_id)

    async def close_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """Close ticket"""
        return await self.update_status(ticket_id, TicketStatus.CLOSED)

    async def get_tickets_waiting_user(self) -> List[Ticket]:
        """Get all tickets waiting for user response"""
        result = await self.session.execute(
            select(Ticket)
            .options(selectinload(Ticket.user))
            .where(Ticket.status == TicketStatus.WAITING_USER)
        )
        return list(result.scalars().all())


class MessageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, ticket_id: int, message_text: Optional[str] = None,
                    user_id: Optional[int] = None, manager_id: Optional[int] = None,
                    sticker_file_id: Optional[str] = None) -> Message:
        """Create new message (text or sticker) and bump the parent ticket's last_activity_at"""
        message = Message(
            ticket_id=ticket_id,
            user_id=user_id,
            manager_id=manager_id,
            message_text=message_text,
            sticker_file_id=sticker_file_id
        )
        self.session.add(message)
        await self.session.execute(
            update(Ticket).where(Ticket.id == ticket_id).values(last_activity_at=datetime.utcnow())
        )
        await self.session.commit()
        await self.session.refresh(message)

        return message

    async def get_ticket_messages(self, ticket_id: int, limit: int = 50) -> List[Message]:
        """Get all messages for ticket"""
        result = await self.session.execute(
            select(Message)
            .options(selectinload(Message.user), selectinload(Message.manager))
            .where(Message.ticket_id == ticket_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        return list(reversed(messages))  # Return in chronological order

