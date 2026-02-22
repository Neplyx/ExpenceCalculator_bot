from aiogram import types
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_menu():
    builder = ReplyKeyboardBuilder()
    # Повертаємо всі 8 кнопок з твого оригінального коду
    builder.add(types.KeyboardButton(text="Загальна сума 💰"))
    builder.add(types.KeyboardButton(text="Історія витрат 📜"))
    builder.add(types.KeyboardButton(text="Витрати 📊"))
    builder.add(types.KeyboardButton(text="Видалити останню ❌"))
    builder.add(types.KeyboardButton(text="Статистика 📊"))
    builder.add(types.KeyboardButton(text="Курс валют 💵"))
    builder.add(types.KeyboardButton(text="Цілі 🎯"))
    builder.add(types.KeyboardButton(text="Ліміти 📉"))
    builder.add(types.KeyboardButton(text="Підписки 🔄"))
    
    builder.adjust(2) # Розташування по 2 кнопки в ряд
    return builder.as_markup(resize_keyboard=True)