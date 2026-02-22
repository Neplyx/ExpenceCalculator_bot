from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        "Загальна сума 💰", "Історія витрат 📜", "Витрати 📊",
        "Видалити останню ❌", "Статистика 📊", "Курс валют 💵",
        "Цілі 🎯", "Ліміти 📉", "Підписки 🔄"
    ]
    for btn in buttons:
        builder.add(KeyboardButton(text=btn))
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)