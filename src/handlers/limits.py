from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter
from datetime import datetime

# Імпорт компонентів з нової структури
from src.utils.states import LimitStates
from src.database import requests as rq
from src.utils.formatter import get_progress_bar
from src.keyboards.main_menu import main_menu_kb

router = Router()

async def render_limits_menu(event: types.Message | types.CallbackQuery):
    """Допоміжна функція для відображення меню лімітів (без змін у логіці текстів)"""
    user_id = event.from_user.id
    # Отримуємо об'єкти лімітів з Postgres
    limits = await rq.get_limits(user_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Додати/Змінити ліміт ➕", callback_data="limit_add")
    
    # ТЕКСТ ТА ОФОРМЛЕННЯ БЕЗ ЗМІН
    text = "📊 <b>МОНІТОРИНГ ЛІМІТІВ</b>\n"
    text += "<code>" + "—" * 20 + "</code>\n\n"
    
    if not limits:
        text += "Ліміти не встановлені. Почніть контролювати витрати вже сьогодні! 📉"
    else:
        for lim in limits:
            # Отримуємо суму витрат за місяць через асинхронний запит
            spent = await rq.get_monthly_category_sum(user_id, lim.category)
            progress = get_progress_bar(spent, lim.amount)
            status = "✅" if spent < lim.amount else "🛑"
            text += f"{status} <b>{lim.category}</b>\n{progress}\n💰 <code>{spent:.2f} / {lim.amount:.2f} грн</code>\n\n"
        
        text += "<code>" + "—" * 20 + "</code>"
        builder.button(text="Видалити ліміт 🗑", callback_data="limit_delete_menu")
    
    builder.adjust(1)
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await event.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.message(F.text == "Ліміти 📉", StateFilter(None))
async def show_limits_message(message: types.Message):
    await render_limits_menu(message)

# --- ДОДАВАННЯ ЛІМІТУ ---

@router.callback_query(F.data == "limit_add", StateFilter("*"))
async def start_limit_add(callback: types.CallbackQuery, state: FSMContext):
    # Повний список твоїх оригінальних категорій
    categories = [
        "Продукти 🛒", "Транспорт 🚕", "Відпочинок ☕", 
        "Дім/Побут 🏠", "Здоров'я 💊", "Техніка 💻",
        "Одяг та взуття 👕", "Краса та догляд ✨", 
        "Донати та подарунки 🎁", "Тварини 🐾"
    ]
    
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat, callback_data=f"setlcat_{cat}")
    builder.adjust(2)
    
    # ТЕКСТ БЕЗ ЗМІН
    text = (
        "🛠 <b>Крок 1: Оберіть категорію</b>\n\n"
        "Для якої сфери витрат ви хочете встановити ліміт?"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.set_state(LimitStates.choosing_category)

@router.callback_query(LimitStates.choosing_category, F.data.startswith("setlcat_"))
async def process_limit_cat(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    await state.update_data(chosen_category=category)
    
    # ТЕКСТ БЕЗ ЗМІН
    text = (
        f"💳 <b>Крок 2: Встановіть суму</b>\n\n"
        f"Який місячний ліміт ви встановите для категорії <b>'{category}'</b>?"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(LimitStates.entering_amount)

@router.message(LimitStates.entering_amount)
async def process_limit_amt(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '', 1).isdigit():
        await message.answer("❌ <b>Помилка:</b> Будь ласка, введіть числове значення.")
        return
    
    amount = float(message.text)
    data = await state.get_data()
    category = data['chosen_category']
    
    # Зберігаємо/оновлюємо в Postgres
    await rq.set_limit(message.from_user.id, category, amount)
    
    # ТЕКСТ БЕЗ ЗМІН
    success_text = (
        f"✅ <b>Ліміт встановлено!</b>\n"
        "<code>" + "—" * 20 + "</code>\n"
        f"📌 <b>Категорія:</b> {category}\n"
        f"💰 <b>Сума:</b> <code>{amount:.2f} грн/міс</code>\n\n"
        "<i>Бот автоматично попередить вас при наближенні до цієї суми.</i>"
    )
    await message.answer(success_text, reply_markup=main_menu_kb(), parse_mode="HTML")
    await state.clear()

# --- ВИДАЛЕННЯ ЛІМІТУ ---

@router.callback_query(F.data == "limit_delete_menu", StateFilter("*"))
async def show_delete_limits_list(callback: types.CallbackQuery):
    limits = await rq.get_limits(callback.from_user.id)
    if not limits:
        await callback.answer("У вас немає лімітів для видалення.")
        return

    builder = InlineKeyboardBuilder()
    for lim in limits:
        builder.button(text=f"Видалити {lim.category} ❌", callback_data=f"limitdel_{lim.category}")
    
    builder.button(text="Назад 🔙", callback_data="limit_back")
    builder.adjust(1)
    
    # ТЕКСТ БЕЗ ЗМІН
    text = (
        "🗑 <b>ВИДАЛЕННЯ ЛІМІТУ</b>\n\n"
        "Оберіть категорію, яку хочете прибрати з моніторингу:"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("limitdel_"), StateFilter("*"))
async def execute_limit_deletion(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    # Видаляємо з Postgres
    await rq.delete_limit(callback.from_user.id, category)
    
    text = f"✅ <b>Успішно:</b> Ліміт для '{category}' видалено."
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "limit_back", StateFilter("*"))
async def limit_back(callback: types.CallbackQuery):
    await render_limits_menu(callback)
    await callback.answer()