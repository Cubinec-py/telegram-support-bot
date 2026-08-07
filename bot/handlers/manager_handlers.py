from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import ManagerRepository, TicketRepository, MessageRepository, UserRepository
from bot.keyboards.keyboards import get_manager_main_keyboard, get_manager_ticket_keyboard, get_ticket_list_keyboard
from bot.utils.i18n import i18n
from bot.utils.language import get_user_language
from bot.utils.notifications import message_preview
from bot.states.states import ManagerStates
from bot.config import settings
from bot.database.models import TicketStatus

router = Router()


def is_manager(telegram_id: int) -> bool:
    """Check if user is manager"""
    return telegram_id in settings.admin_ids_list


@router.message(Command("manager"))
async def cmd_manager_panel(message: Message, session: AsyncSession):
    """Show manager panel"""
    if not is_manager(message.from_user.id):
        await message.answer(i18n.get("errors.permission_denied"))
        return

    manager_repo = ManagerRepository(session)
    manager = await manager_repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name or "Manager"
    )

    ticket_repo = TicketRepository(session)
    active_tickets = await ticket_repo.get_manager_active_tickets(manager.id)
    unassigned_tickets = await ticket_repo.get_unassigned_tickets()

    manager_language = await get_user_language(session, message.from_user.id)
    panel_text = i18n.get(
        "manager.panel",
        manager_language,
        active_count=len(active_tickets),
        unassigned_count=len(unassigned_tickets)
    )

    panel_text += "\n\n💡 Используйте кнопки ниже или выберите действие:"

    await message.answer(
        panel_text,
        reply_markup=get_manager_main_keyboard()
    )


@router.callback_query(F.data == "manager_panel")
async def show_manager_panel(callback: CallbackQuery, session: AsyncSession):
    """Show manager panel"""
    if not is_manager(callback.from_user.id):
        await callback.answer(i18n.get("errors.permission_denied"), show_alert=True)
        return

    manager_repo = ManagerRepository(session)
    manager = await manager_repo.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name or "Manager"
    )

    ticket_repo = TicketRepository(session)
    active_tickets = await ticket_repo.get_manager_active_tickets(manager.id)
    unassigned_tickets = await ticket_repo.get_unassigned_tickets()

    manager_language = await get_user_language(session, callback.from_user.id)
    panel_text = i18n.get(
        "manager.panel",
        manager_language,
        active_count=len(active_tickets),
        unassigned_count=len(unassigned_tickets)
    )

    await callback.message.edit_text(
        panel_text,
        reply_markup=get_manager_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "manager_my_tickets")
async def show_my_tickets_manager(callback: CallbackQuery, session: AsyncSession):
    """Show manager's active tickets"""
    if not is_manager(callback.from_user.id):
        await callback.answer(i18n.get("errors.permission_denied"), show_alert=True)
        return

    manager_repo = ManagerRepository(session)
    manager = await manager_repo.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name or "Manager"
    )

    ticket_repo = TicketRepository(session)
    tickets = await ticket_repo.get_manager_active_tickets(manager.id)

    if not tickets:
        await callback.answer(i18n.get("manager.no_active_tickets"), show_alert=True)
        return

    await callback.message.edit_text(
        "📋 Ваши активные тикеты:",
        reply_markup=get_ticket_list_keyboard(tickets, "manager_view_my")
    )
    await callback.answer()


@router.callback_query(F.data == "manager_new_tickets")
async def show_new_tickets(callback: CallbackQuery, session: AsyncSession):
    """Show unassigned tickets"""
    if not is_manager(callback.from_user.id):
        await callback.answer(i18n.get("errors.permission_denied"), show_alert=True)
        return

    ticket_repo = TicketRepository(session)
    tickets = await ticket_repo.get_unassigned_tickets()

    if not tickets:
        await callback.answer(i18n.get("manager.no_unassigned"), show_alert=True)
        return

    await callback.message.edit_text(
        "🆕 Новые тикеты:",
        reply_markup=get_ticket_list_keyboard(tickets, "manager_view_new")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("manager_view_my_ticket_") | F.data.startswith("manager_view_new_ticket_"))
async def view_ticket(callback: CallbackQuery, session: AsyncSession):
    """View ticket details"""
    if not is_manager(callback.from_user.id):
        await callback.answer(i18n.get("errors.permission_denied"), show_alert=True)
        return

    try:
        ticket_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer(i18n.get("errors.general"), show_alert=True)
        return

    # Remember which list this ticket was opened from so "Back" returns
    # there instead of always bouncing to the general panel
    back_callback = "manager_my_tickets" if callback.data.startswith("manager_view_my_ticket_") else "manager_new_tickets"

    ticket_repo = TicketRepository(session)
    ticket = await ticket_repo.get_by_id(ticket_id)

    if not ticket:
        await callback.answer(i18n.get("errors.ticket_not_found"), show_alert=True)
        return

    manager_language = await get_user_language(session, callback.from_user.id)

    # Get last messages
    message_repo = MessageRepository(session)
    messages = await message_repo.get_ticket_messages(ticket_id, limit=5)

    last_message = message_preview(messages[-1].message_text, manager_language) if messages else "Нет сообщений"

    user = ticket.user
    username = user.username if user.username else "нет"
    user_name = user.first_name or f"User {user.telegram_id}"
    user_id = user.telegram_id
    created_at = ticket.created_at.strftime("%d.%m.%Y %H:%M")
    status = i18n.get(f"status.{ticket.status}", manager_language)

    ticket_info = i18n.get(
        "manager.ticket_info",
        manager_language,
        ticket_number=ticket.ticket_number,
        user_name=user_name,
        username=username,
        user_id=user_id,
        created_at=created_at,
        status=status,
        last_message=last_message[:200]
    )

    await callback.message.edit_text(
        ticket_info,
        reply_markup=get_manager_ticket_keyboard(ticket.id, ticket.ticket_number, back_callback=back_callback),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("manager_assign_"))
async def assign_ticket(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Assign ticket to manager"""
    if not is_manager(callback.from_user.id):
        await callback.answer(i18n.get("errors.permission_denied"), show_alert=True)
        return

    try:
        ticket_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer(i18n.get("errors.general"), show_alert=True)
        return

    manager_language = await get_user_language(session, callback.from_user.id)

    manager_repo = ManagerRepository(session)
    manager = await manager_repo.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name or "Manager"
    )

    ticket_repo = TicketRepository(session)
    ticket = await ticket_repo.assign_manager(ticket_id, manager.id)

    if ticket:
        await callback.answer(
            i18n.get("manager.assigned", manager_language, ticket_number=ticket.ticket_number),
            show_alert=True
        )

        # Notify user
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(ticket.user.telegram_id)

        if user:
            from bot.utils.notifications import notify_user_manager_assigned
            await notify_user_manager_assigned(
                bot,
                user.telegram_id,
                ticket.ticket_number,
                manager.first_name,
                user.language
            )

        # Refresh view - show ticket info again
        ticket = await ticket_repo.get_by_id(ticket_id)
        message_repo = MessageRepository(session)
        messages = await message_repo.get_ticket_messages(ticket_id, limit=5)
        last_message = message_preview(messages[-1].message_text, manager_language) if messages else "Нет сообщений"

        user = ticket.user
        username = user.username if user.username else "нет"
        user_name = user.first_name or f"User {user.telegram_id}"
        user_id = user.telegram_id
        created_at = ticket.created_at.strftime("%d.%m.%Y %H:%M")
        status = i18n.get(f"status.{ticket.status}", manager_language)

        ticket_info = i18n.get(
            "manager.ticket_info",
            manager_language,
            ticket_number=ticket.ticket_number,
            user_name=user_name,
            username=username,
            user_id=user_id,
            created_at=created_at,
            status=status,
            last_message=last_message[:200]
        )

        # Just claimed from the unassigned queue, so it now belongs under
        # "my tickets" rather than "new tickets"
        await callback.message.edit_text(
            ticket_info,
            reply_markup=get_manager_ticket_keyboard(ticket.id, ticket.ticket_number, back_callback="manager_my_tickets"),
            parse_mode="HTML"
        )
    else:
        # Either the ticket doesn't exist, or another manager already claimed it
        # (assign_manager() returns None for both — this is the race-safety path)
        existing = await ticket_repo.get_by_id(ticket_id)
        error_key = "errors.already_assigned" if existing else "errors.ticket_not_found"
        await callback.answer(i18n.get(error_key, manager_language), show_alert=True)


@router.callback_query(F.data.startswith("manager_reply_"))
async def start_reply(callback: CallbackQuery, state: FSMContext):
    """Start reply to ticket"""
    if not is_manager(callback.from_user.id):
        await callback.answer(i18n.get("errors.permission_denied"), show_alert=True)
        return

    try:
        ticket_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer(i18n.get("errors.general"), show_alert=True)
        return

    await state.set_state(ManagerStates.waiting_reply)
    await state.update_data(reply_ticket_id=ticket_id)

    await callback.message.answer(
        "💬 Введите ответ пользователю:\n\n(Для отмены используйте /cancel)"
    )
    await callback.answer()


@router.message(ManagerStates.waiting_reply, Command("cancel"))
async def cancel_reply(message: Message, state: FSMContext):
    """Cancel reply"""
    await state.clear()
    await message.answer("❌ Отправка сообщения отменена.")


@router.message(ManagerStates.waiting_reply)
async def send_reply(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Send reply to user"""
    if not is_manager(message.from_user.id):
        return

    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")

    if not ticket_id:
        await state.clear()
        return

    sticker_file_id = message.sticker.file_id if message.sticker else None
    if not message.text and not sticker_file_id:
        manager_language = await get_user_language(session, message.from_user.id)
        await message.answer(i18n.get("errors.text_only", manager_language))
        return

    manager_repo = ManagerRepository(session)
    manager = await manager_repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name or "Manager"
    )

    ticket_repo = TicketRepository(session)
    ticket = await ticket_repo.get_by_id(ticket_id)

    if not ticket:
        await message.answer(i18n.get("errors.ticket_not_found"))
        await state.clear()
        return

    # Save message
    message_repo = MessageRepository(session)
    await message_repo.create(
        ticket_id=ticket_id,
        manager_id=manager.id,
        message_text=message.text,
        sticker_file_id=sticker_file_id
    )

    # Update ticket status
    await ticket_repo.update_status(ticket_id, TicketStatus.WAITING_USER)

    # Send to user
    user = ticket.user
    user_repo = UserRepository(session)
    user_obj = await user_repo.get_by_telegram_id(user.telegram_id)

    if user_obj:
        from bot.utils.notifications import send_message_to_user
        await send_message_to_user(
            bot,
            user.telegram_id,
            ticket.ticket_number,
            message.text,
            user_obj.language,
            sticker_file_id
        )

    await message.answer(i18n.get("manager.message_sent"))
    await state.clear()


@router.callback_query(F.data.startswith("manager_close_"))
async def close_ticket_manager(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Close ticket by manager"""
    if not is_manager(callback.from_user.id):
        await callback.answer(i18n.get("errors.permission_denied"), show_alert=True)
        return

    try:
        ticket_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer(i18n.get("errors.general"), show_alert=True)
        return

    ticket_repo = TicketRepository(session)
    ticket = await ticket_repo.close_ticket(ticket_id)

    if ticket:
        await callback.answer(f"✅ Тикет {ticket.ticket_number} закрыт", show_alert=True)

        # Notify user
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(ticket.user.telegram_id)

        if user:
            from bot.utils.notifications import notify_user_ticket_closed
            await notify_user_ticket_closed(
                bot,
                user.telegram_id,
                ticket.ticket_number,
                user.language
            )

        # Return to panel
        await show_manager_panel(callback, session)
    else:
        # Either the ticket doesn't exist, or it was already closed by someone
        # else (another manager, or the auto-close scheduler) — update_status()
        # returns None for both, which is what makes close_ticket() idempotent
        manager_language = await get_user_language(session, callback.from_user.id)
        existing = await ticket_repo.get_by_id(ticket_id)
        error_key = "errors.already_closed" if existing else "errors.ticket_not_found"
        await callback.answer(i18n.get(error_key, manager_language), show_alert=True)


@router.callback_query(F.data == "manager_stats")
async def show_stats(callback: CallbackQuery, session: AsyncSession):
    """Show manager statistics"""
    if not is_manager(callback.from_user.id):
        await callback.answer(i18n.get("errors.permission_denied"), show_alert=True)
        return

    manager_repo = ManagerRepository(session)
    manager = await manager_repo.get_or_create(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name or "Manager"
    )

    ticket_repo = TicketRepository(session)
    active_tickets = await ticket_repo.get_manager_active_tickets(manager.id)

    # Simple stats for now
    stats_text = f"📊 Статистика\n\n"
    stats_text += f"Активных тикетов: {len(active_tickets)}\n"

    await callback.answer(stats_text, show_alert=True)

