from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
# Імпортуємо наш новий репозиторій для роботи з Postgres
from src.database import requests as rq
# Імпортуємо клавіатуру з нової структури
from src.keyboards.main_menu import main_menu_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    # ТИХА РЕЄСТРАЦІЯ: додаємо юзера в Postgres
    await rq.add_user(message.from_user.id, message.from_user.username)
    
    # ТЕКСТ ЗАЛИШЕНО БЕЗ ЗМІН
    user_name = message.from_user.first_name
    welcome_text = (
        f"👋 <b>ПРИВІТ, {user_name.upper()}!</b>\n"
        f"<code>" + "—" * 20 + "</code>\n\n"
        "Я твій інтелектуальний помічник для контролю фінансів. 💸\n\n"
        "Обери дію в меню нижче або просто <b>введи витрату</b> (наприклад: <code>150 кава</code>) і я автоматично її категоризую.\n\n"
        f"<code>" + "—" * 20 + "</code>\n"
        "<i>Разом до фінансової свободи!</i> 🚀"
    )
    await message.answer(welcome_text, reply_markup=main_menu_kb(), parse_mode="HTML")

@router.message(Command("cancel"))
@router.message(F.text.casefold() == "скасувати")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    # ТЕКСТ ЗАЛИШЕНО БЕЗ ЗМІН
    await message.answer("🔙 <b>ДІЮ СКАСОВАНО</b>", reply_markup=main_menu_kb(), parse_mode="HTML")