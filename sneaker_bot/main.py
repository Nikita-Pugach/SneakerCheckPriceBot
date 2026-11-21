import asyncio
import logging

from sneaker_bot.setting import bot, dp
from sneaker_bot.startup import set_commands

from sneaker_bot.handlers import router as main_router

dp.include_router(main_router)


async def main():
    await set_commands(bot)
    await dp.start_polling(bot, skip_updates=False)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(main())
