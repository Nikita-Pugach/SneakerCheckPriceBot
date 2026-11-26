from aiogram import Bot
from aiogram.types import BotCommand


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="help", description="Как пользоваться"),
    ]
    await bot.set_my_commands(commands)
