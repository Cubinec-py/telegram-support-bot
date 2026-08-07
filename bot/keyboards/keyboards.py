from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from bot.utils.i18n import i18n


def get_main_keyboard(language: str = "ru", is_manager: bool = False) -> ReplyKeyboardMarkup:
    """Main menu keyboard"""
    builder = ReplyKeyboardBuilder()

    if is_manager:
        # Manager keyboard
        builder.row(
            KeyboardButton(text=i18n.get("buttons.manager_panel", language))
        )
        builder.row(
            KeyboardButton(text=i18n.get("buttons.new_tickets", language)),
            KeyboardButton(text=i18n.get("buttons.my_manager_tickets", language))
        )
        builder.row(
            KeyboardButton(text=i18n.get("buttons.change_language", language))
        )
    else:
        # Regular user keyboard
        builder.row(
            KeyboardButton(text=i18n.get("buttons.new_ticket", language))
        )
        builder.row(
            KeyboardButton(text=i18n.get("buttons.my_tickets", language)),
            KeyboardButton(text=i18n.get("buttons.change_language", language))
        )

    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Cancel keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=i18n.get("buttons.cancel", language))
    )
    return builder.as_markup(resize_keyboard=True)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Language selection keyboard"""
    builder = InlineKeyboardBuilder()
    languages = {
        "ru": "🇷🇺 Русский",
        "en": "🇬🇧 English",
        "es": "🇪🇸 Español",
        "uk": "🇺🇦 Українська"
    }

    for lang_code, lang_name in languages.items():
        builder.row(
            InlineKeyboardButton(text=lang_name, callback_data=f"lang_{lang_code}")
        )

    return builder.as_markup()


def get_ticket_keyboard(ticket_id: int, language: str = "ru") -> InlineKeyboardMarkup:
    """Ticket actions keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=i18n.get("buttons.close_ticket", language),
            callback_data=f"close_ticket_{ticket_id}"
        )
    )
    return builder.as_markup()


def get_manager_main_keyboard() -> InlineKeyboardMarkup:
    """Manager main menu keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Мои тикеты", callback_data="manager_my_tickets")
    )
    builder.row(
        InlineKeyboardButton(text="🆕 Новые тикеты", callback_data="manager_new_tickets")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="manager_stats")
    )
    return builder.as_markup()


def get_manager_ticket_keyboard(ticket_id: int, ticket_number: str) -> InlineKeyboardMarkup:
    """Manager ticket actions keyboard"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Взять в работу", callback_data=f"manager_assign_{ticket_id}")
    )
    builder.row(
        InlineKeyboardButton(text="💬 Ответить", callback_data=f"manager_reply_{ticket_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔒 Закрыть", callback_data=f"manager_close_{ticket_id}")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="manager_panel")
    )
    return builder.as_markup()


def get_ticket_list_keyboard(tickets: list, prefix: str = "view", back_callback: str = "manager_panel") -> InlineKeyboardMarkup:
    """Keyboard with list of tickets"""
    builder = InlineKeyboardBuilder()

    for ticket in tickets:
        status_emoji = {
            "open": "🆕",
            "in_progress": "⏳",
            "waiting_user": "⌛",
            "closed": "✅"
        }.get(ticket.status, "📋")

        builder.row(
            InlineKeyboardButton(
                text=f"{status_emoji} {ticket.ticket_number}",
                callback_data=f"{prefix}_ticket_{ticket.id}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)
    )

    return builder.as_markup()

