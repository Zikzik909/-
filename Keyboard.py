from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

kb = ReplyKeyboardMarkup(
    keyboard=[
            [KeyboardButton(text="/inventory"), KeyboardButton(text="/status")],
            [KeyboardButton(text="/register"), KeyboardButton(text="/orders")],
            [KeyboardButton(text="/info")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите что вам необходимо"
)
