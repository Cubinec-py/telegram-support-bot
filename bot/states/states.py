from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """User FSM states"""
    waiting_ticket_description = State()
    in_ticket_conversation = State()


class ManagerStates(StatesGroup):
    """Manager FSM states"""
    waiting_reply = State()

