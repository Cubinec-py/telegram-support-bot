from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Text, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


class UserLanguage(str, enum.Enum):
    RU = "ru"
    EN = "en"
    ES = "es"
    UK = "uk"

    def __str__(self) -> str:
        # Without this, f"{UserLanguage.RU}" gives "UserLanguage.RU" instead
        # of "ru" — Enum's default __str__ wins over the str mixin
        return self.value


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    CLOSED = "closed"

    def __str__(self) -> str:
        return self.value


class ManagerStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"

    def __str__(self) -> str:
        return self.value


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(SQLEnum(UserLanguage), default=UserLanguage.RU)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Manager(Base):
    __tablename__ = "managers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(SQLEnum(ManagerStatus), default=ManagerStatus.OFFLINE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="manager")
    messages: Mapped[list["Message"]] = relationship(back_populates="manager")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    manager_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("managers.id"), nullable=True)
    status: Mapped[str] = mapped_column(SQLEnum(TicketStatus), default=TicketStatus.OPEN)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Updated only when a new message is posted (unlike updated_at, which also
    # changes on manager-side reads/status changes) — this is what the
    # auto-close scheduler checks to decide whether a ticket is truly idle.
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="tickets")
    manager: Mapped[Optional["Manager"]] = relationship(back_populates="tickets")
    messages: Mapped[list["Message"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tickets.id"))
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    manager_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("managers.id"), nullable=True)
    message_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    ticket: Mapped["Ticket"] = relationship(back_populates="messages")
    user: Mapped[Optional["User"]] = relationship(back_populates="messages")
    manager: Mapped[Optional["Manager"]] = relationship(back_populates="messages")

    @property
    def is_from_user(self) -> bool:
        return self.user_id is not None

