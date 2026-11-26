"""The /help command: what the bot does and how to use it."""

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from sneaker_bot.menu.back_menu import back_menu
from sneaker_bot.services.send_messages import record_and_send

router = Router()
logger = logging.getLogger(__name__)

HELP_TEXT = (
    "🤖 <b>SneakerCheckPriceBot</b>\n"
    "\n"
    "Сравниваю цены на кроссовки в трёх местах: <b>bunt.by</b>, "
    "<b>sneakers.by</b> и <b>kufar.by</b>. Показываю, где дешевле.\n"
    "\n"
    "<b>Как искать</b>\n"
    "• кнопками: «Узнать цены» → бренд → модель → размер\n"
    "• или просто напишите: <i>nike air max 42</i>\n"
    "\n"
    "<b>Что есть в результатах</b>\n"
    "• минимум и средняя цена по всем магазинам\n"
    "• фильтр по цене: до 200 / 300 / 500\n"
    "• новые или б/у (у Kufar видно состояние и город)\n"
    "• «Показать ещё», если предложений много\n"
    "\n"
    "<b>История</b>\n"
    "Каждый поиск сохраняется: нажмите «История» в меню и повторите "
    "любой запрос одним касанием. Если цена изменилась с прошлого раза, "
    "бот это отметит.\n"
    "\n"
    "Команды: /start — меню, /help — эта справка.\n"
    "\n"
    "Исходный код и описание: "
    '<a href="https://github.com/Nikita-Pugach/SneakerCheckPriceBot">GitHub</a>'
)


@router.message(Command("help"))
async def help_command(message: Message, state: FSMContext) -> None:
    await record_and_send(message, state, text=HELP_TEXT, reply_markup=back_menu)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


@router.callback_query(F.data == "help_button")
async def help_button(query, state: FSMContext) -> None:
    try:
        await query.answer(cache_time=2)
    except TelegramBadRequest:
        pass
    await record_and_send(query, state, text=HELP_TEXT, reply_markup=back_menu)
