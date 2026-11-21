import logging
import os
from functools import wraps

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv

from sneaker_bot.setting import bot

load_dotenv()
ID_CHANNEL = os.getenv("ID_CHANNEL")

logger = logging.getLogger(__name__)

NOT_SUBSCRIBED = "Чтобы пользоваться, подпишись на канал"


async def checker_sub(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=ID_CHANNEL, user_id=user_id)
    except TelegramBadRequest as exc:
        # A wrong channel id, or the bot is not an admin there. Failing open keeps
        # the bot usable instead of locking every user out because of a config typo.
        logger.warning("subscription check failed for channel %s: %s", ID_CHANNEL, exc)
        return True
    return member.status not in ("left", "kicked")


def is_sub(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        message = None
        query = None
        for arg in args:
            if isinstance(arg, Message):
                message = arg
            elif isinstance(arg, CallbackQuery):
                query = arg

        if query is not None:
            user_id = query.from_user.id
        elif message is not None:
            user_id = message.from_user.id
        else:
            return await func(*args, **kwargs)

        if not await checker_sub(bot, user_id):
            # A callback can show an alert; a plain message cannot, which is why
            # this used to crash with AttributeError when the user typed text.
            if query is not None:
                await query.answer(NOT_SUBSCRIBED, show_alert=True)
            elif message is not None:
                await message.answer(NOT_SUBSCRIBED)
            return None

        return await func(*args, **kwargs)

    return wrapper
