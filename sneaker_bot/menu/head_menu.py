from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

REPO_URL = "https://github.com/Nikita-Pugach/SneakerCheckPriceBot"

head_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔍Узнать цены🔍",
                callback_data="know_button"
            ),
            InlineKeyboardButton(
                text="📰Новости📰",
                callback_data="news_button"
            )
        ],
        [
            InlineKeyboardButton(
                text="🕓История🕓",
                callback_data="history_button"
            ),
            InlineKeyboardButton(
                text="❓Помощь❓",
                callback_data="help_button"
            )
        ],
    ]
)
