from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.repositories import UserRepository, TicketRepository, MessageRepository
from bot.keyboards.keyboards import get_main_keyboard, get_cancel_keyboard, get_language_keyboard
from bot.utils.i18n import i18n
from bot.utils.language import get_user_language
from bot.states.states import UserStates
from bot.config import settings

router = Router()


def is_manager(telegram_id: int) -> bool:
    """Check if user is manager"""
    return telegram_id in settings.admin_ids_list


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    """Handle /start command"""
    await state.clear()

    user_repo = UserRepository(session)
    user = await user_repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language=settings.DEFAULT_LANGUAGE
    )

    # Check if user is manager
    is_manager = message.from_user.id in settings.admin_ids_list

    welcome_text = i18n.get("start.welcome", user.language)
    action_text = i18n.get("start.choose_action", user.language)

    if is_manager:
        welcome_text += "\n\n👨‍💼 <b>Вы вошли как менеджер</b>"

    await message.answer(
        f"{welcome_text}\n\n{action_text}",
        reply_markup=get_main_keyboard(user.language, is_manager=is_manager),
        parse_mode="HTML"
    )


@router.message(F.text.in_([
    i18n.get("buttons.new_ticket", "ru"),
    i18n.get("buttons.new_ticket", "en"),
    i18n.get("buttons.new_ticket", "es"),
    i18n.get("buttons.new_ticket", "uk"),
]))
async def create_ticket_start(message: Message, session: AsyncSession, state: FSMContext):
    """Start ticket creation"""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer(i18n.get("errors.general"))
        return

    # Check active tickets limit
    ticket_repo = TicketRepository(session)
    active_tickets = await ticket_repo.get_user_active_tickets(user.id)

    if len(active_tickets) >= settings.MAX_ACTIVE_TICKETS_PER_USER:
        await message.answer(
            i18n.get("tickets.max_reached", user.language, max=settings.MAX_ACTIVE_TICKETS_PER_USER),
            reply_markup=get_main_keyboard(user.language, is_manager=is_manager(message.from_user.id))
        )
        return

    await message.answer(
        i18n.get("tickets.create_prompt", user.language),
        reply_markup=get_cancel_keyboard(user.language)
    )
    await state.set_state(UserStates.waiting_ticket_description)


@router.message(UserStates.waiting_ticket_description, F.text.in_([
    i18n.get("buttons.cancel", "ru"),
    i18n.get("buttons.cancel", "en"),
    i18n.get("buttons.cancel", "es"),
    i18n.get("buttons.cancel", "uk"),
]))
async def cancel_ticket_creation(message: Message, session: AsyncSession, state: FSMContext):
    """Cancel ticket creation"""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    await state.clear()
    await message.answer(
        i18n.get("start.choose_action", user.language if user else "ru"),
        reply_markup=get_main_keyboard(user.language if user else "ru", is_manager=is_manager(message.from_user.id))
    )


@router.message(UserStates.waiting_ticket_description)
async def create_ticket_finish(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Finish ticket creation"""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer(i18n.get("errors.general"))
        return

    # Create ticket
    ticket_repo = TicketRepository(session)
    ticket = await ticket_repo.create(user_id=user.id, subject=message.text[:500])

    # Save first message
    message_repo = MessageRepository(session)
    await message_repo.create(
        ticket_id=ticket.id,
        user_id=user.id,
        message_text=message.text
    )

    # Auto-assign to the available manager with the fewest active tickets
    from bot.database.repositories import ManagerRepository
    manager_repo = ManagerRepository(session)
    available_manager = await manager_repo.get_and_lock_least_busy_manager()

    if available_manager:
        assigned_ticket = await ticket_repo.assign_manager(ticket.id, available_manager.id)

        if assigned_ticket:
            # Notify manager
            from bot.utils.notifications import notify_manager_new_ticket
            manager_language = await get_user_language(session, available_manager.telegram_id)
            await notify_manager_new_ticket(bot, available_manager.telegram_id, ticket, user, message.text, manager_language)

    await state.clear()
    await message.answer(
        i18n.get("tickets.created", user.language, ticket_number=ticket.ticket_number),
        reply_markup=get_main_keyboard(user.language, is_manager=is_manager(message.from_user.id))
    )

    # Save ticket ID for conversation
    await state.update_data(current_ticket_id=ticket.id)
    await state.set_state(UserStates.in_ticket_conversation)


@router.message(F.text.in_([
    i18n.get("buttons.my_tickets", "ru"),
    i18n.get("buttons.my_tickets", "en"),
    i18n.get("buttons.my_tickets", "es"),
    i18n.get("buttons.my_tickets", "uk"),
]))
async def show_my_tickets(message: Message, session: AsyncSession):
    """Show user's active tickets"""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer(i18n.get("errors.general"))
        return

    ticket_repo = TicketRepository(session)
    tickets = await ticket_repo.get_user_active_tickets(user.id)

    if not tickets:
        await message.answer(
            i18n.get("tickets.no_active", user.language),
            reply_markup=get_main_keyboard(user.language, is_manager=is_manager(message.from_user.id))
        )
        return

    text = i18n.get("tickets.list_header", user.language)

    for ticket in tickets:
        status_text = i18n.get(f"status.{ticket.status}", user.language)
        created_at = ticket.created_at.strftime("%d.%m.%Y %H:%M")

        ticket_text = i18n.get(
            "tickets.item",
            user.language,
            ticket_number=ticket.ticket_number,
            status=status_text,
            created_at=created_at
        )
        text += f"\n{ticket_text}\n"

    await message.answer(text, reply_markup=get_main_keyboard(user.language, is_manager=is_manager(message.from_user.id)))


@router.message(F.text.in_([
    i18n.get("buttons.change_language", "ru"),
    i18n.get("buttons.change_language", "en"),
    i18n.get("buttons.change_language", "es"),
    i18n.get("buttons.change_language", "uk"),
]))
async def change_language(message: Message, session: AsyncSession):
    """Show language selection"""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    await message.answer(
        i18n.get("language.select", user.language if user else "ru"),
        reply_markup=get_language_keyboard()
    )


@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery, session: AsyncSession):
    """Set user language"""
    language = callback.data.split("_")[1]

    user_repo = UserRepository(session)
    await user_repo.update_language(callback.from_user.id, language)

    await callback.message.edit_text(
        i18n.get("language.changed", language)
    )

    await callback.message.answer(
        i18n.get("start.choose_action", language),
        reply_markup=get_main_keyboard(language, is_manager=is_manager(callback.from_user.id))
    )

    await callback.answer()


@router.callback_query(F.data.startswith("close_ticket_"))
async def close_ticket(callback: CallbackQuery, session: AsyncSession):
    """Close ticket"""
    try:
        ticket_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        await callback.answer(i18n.get("errors.general"), show_alert=True)
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer(i18n.get("errors.general"))
        return

    ticket_repo = TicketRepository(session)
    ticket = await ticket_repo.get_by_id(ticket_id)

    if not ticket or ticket.user_id != user.id:
        await callback.answer(i18n.get("errors.ticket_not_found", user.language))
        return

    closed_ticket = await ticket_repo.close_ticket(ticket_id)

    if not closed_ticket:
        await callback.answer(i18n.get("errors.already_closed", user.language), show_alert=True)
        return

    await callback.message.edit_text(
        i18n.get("tickets.closed", user.language, ticket_number=ticket.ticket_number)
    )

    await callback.answer()


@router.message(UserStates.in_ticket_conversation)
async def handle_ticket_message(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Handle message in ticket conversation"""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if not user:
        return

    data = await state.get_data()
    ticket_id = data.get("current_ticket_id")

    if not ticket_id:
        # Get latest active ticket
        ticket_repo = TicketRepository(session)
        tickets = await ticket_repo.get_user_active_tickets(user.id)
        if tickets:
            ticket_id = tickets[0].id
            await state.update_data(current_ticket_id=ticket_id)

    if ticket_id:
        # Save message
        message_repo = MessageRepository(session)
        await message_repo.create(
            ticket_id=ticket_id,
            user_id=user.id,
            message_text=message.text
        )

        # Notify manager if assigned
        ticket_repo = TicketRepository(session)
        ticket = await ticket_repo.get_by_id(ticket_id)

        if ticket and ticket.manager_id:
            from bot.utils.notifications import notify_manager_new_message
            manager_language = await get_user_language(session, ticket.manager.telegram_id)
            await notify_manager_new_message(bot, ticket.manager.telegram_id, ticket, message.text, manager_language)


# Manager button handlers
@router.message(F.text.in_([
    i18n.get("buttons.manager_panel", "ru"),
    i18n.get("buttons.manager_panel", "en"),
    i18n.get("buttons.manager_panel", "es"),
    i18n.get("buttons.manager_panel", "uk"),
]))
async def manager_panel_button(message: Message, session: AsyncSession):
    """Handle manager panel button"""
    if message.from_user.id not in settings.admin_ids_list:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        await message.answer(i18n.get("errors.permission_denied", user.language if user else "ru"))
        return

    from bot.database.repositories import ManagerRepository, TicketRepository

    manager_repo = ManagerRepository(session)
    manager = await manager_repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name or "Manager"
    )

    ticket_repo = TicketRepository(session)
    active_tickets = await ticket_repo.get_manager_active_tickets(manager.id)
    unassigned_tickets = await ticket_repo.get_unassigned_tickets()

    from bot.keyboards.keyboards import get_manager_main_keyboard

    manager_language = await get_user_language(session, message.from_user.id)
    panel_text = i18n.get(
        "manager.panel",
        manager_language,
        active_count=len(active_tickets),
        unassigned_count=len(unassigned_tickets)
    )

    await message.answer(
        panel_text,
        reply_markup=get_manager_main_keyboard()
    )


@router.message(F.text.in_([
    i18n.get("buttons.new_tickets", "ru"),
    i18n.get("buttons.new_tickets", "en"),
    i18n.get("buttons.new_tickets", "es"),
    i18n.get("buttons.new_tickets", "uk"),
]))
async def new_tickets_button(message: Message, session: AsyncSession):
    """Handle new tickets button"""
    if message.from_user.id not in settings.admin_ids_list:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        await message.answer(i18n.get("errors.permission_denied", user.language if user else "ru"))
        return

    from bot.database.repositories import TicketRepository
    from bot.keyboards.keyboards import get_ticket_list_keyboard

    ticket_repo = TicketRepository(session)
    tickets = await ticket_repo.get_unassigned_tickets()

    if not tickets:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        await message.answer(i18n.get("manager.no_unassigned", user.language if user else "ru"))
        return

    await message.answer(
        i18n.get("buttons.new_tickets", user.language if user else "ru") + ":",
        reply_markup=get_ticket_list_keyboard(tickets, "manager_view")
    )


@router.message(F.text.in_([
    i18n.get("buttons.my_manager_tickets", "ru"),
    i18n.get("buttons.my_manager_tickets", "en"),
    i18n.get("buttons.my_manager_tickets", "es"),
    i18n.get("buttons.my_manager_tickets", "uk"),
]))
async def my_tickets_manager_button(message: Message, session: AsyncSession):
    """Handle manager's my tickets button"""
    if message.from_user.id not in settings.admin_ids_list:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        await message.answer(i18n.get("errors.permission_denied", user.language if user else "ru"))
        return

    # Manager's tickets
    from bot.database.repositories import ManagerRepository, TicketRepository
    from bot.keyboards.keyboards import get_ticket_list_keyboard

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    manager_repo = ManagerRepository(session)
    manager = await manager_repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name or "Manager"
    )

    ticket_repo = TicketRepository(session)
    tickets = await ticket_repo.get_manager_active_tickets(manager.id)

    if not tickets:
        await message.answer(i18n.get("manager.no_active_tickets", user.language if user else "ru"))
        return

    await message.answer(
        i18n.get("buttons.my_manager_tickets", user.language if user else "ru") + ":",
        reply_markup=get_ticket_list_keyboard(tickets, "manager_view")
    )

