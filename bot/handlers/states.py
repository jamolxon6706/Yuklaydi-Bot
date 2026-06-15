from aiogram.fsm.state import State, StatesGroup


class AdminFSM(StatesGroup):
    # Broadcast
    broadcast_content = State()
    broadcast_button = State()
    broadcast_confirm = State()

    # Edit welcome message
    welcome_lang = State()
    welcome_new_text = State()
    welcome_confirm = State()

    # Ban / Unban
    ban_get_id = State()
    unban_get_id = State()

    # Required channel
    channel_set = State()
