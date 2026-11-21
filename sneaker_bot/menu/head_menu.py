from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

REPO_URL = "https://github.com/Nikita-Pugach/SneakerCheckPriceBot"

head_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="❓Узнать цены❓",
                callback_data="know_button"
            ),
            InlineKeyboardButton(
                text="🆕Новости🆕",
                callback_data="news_button"
            )
        ],
        [
            InlineKeyboardButton(
                text="🤝Помощь🤝",
                url=REPO_URL
            )
        ],
    ]
)
