from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter
from states import LimitStates
import database as db
from utils.formatter import get_progress_bar
from datetime import datetime
from handlers.keyboard import main_menu 

router = Router()

async def render_limits_menu(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    limits = db.get_limits(user_id)
    
    # Початок поточного місяця для фільтрації витрат
    month_start = datetime.now().strftime("%Y-%m-01")
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Додати/Змінити ліміт ➕", callback_data="limit_add")
    
    if not limits:
        text = (
            "📉 <b>ЛІМІТИ НЕ ВСТАНОВЛЕНІ</b>\n"
            "<code>" + "—" * 20 + "</code>\n\n"
            "Контроль витрат — це перший крок до фінансової свободи! "
            "Встановіть ліміти на категорії, щоб не витрачати зайвого."
        )
    else:
        text = "📊 <b>МОНІТОРИНГ ЛІМІТІВ:</b>\n"
        text += "<code>" + "—" * 20 + "</code>\n\n"
        
        for category, limit_amount in limits:
            current_spent = db.get_month_sum_by_category(user_id, category, month_start)
            progress = get_progress_bar(current_spent, limit_amount)
            
            # Визначаємо статус ліміту
            status = "✅" if current_spent < limit_amount else "🛑"
            
            text += (
                f"{status} <b>{category}</b>\n"
                f"{progress}\n"
                f"💰 <code>{current_spent:.2f} / {limit_amount:.2f} грн</code>\n\n"
            )
        
        text += "<code>" + "—" * 20 + "</code>"
        builder.button(text="Видалити ліміт 🗑", callback_data="limit_delete_menu")
    
    builder.adjust(1)
    
    if isinstance(event, types.Message):
        await event.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await event.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.message(F.text == "Ліміти 📉", StateFilter("*"))
async def show_limits_message(message: types.Message):
    await render_limits_menu(message)

# --- ДОДАВАННЯ ЛІМІТУ (ОНОВЛЕНО: ВСІ 10 КАТЕГОРІЙ) ---
@router.callback_query(F.data == "limit_add", StateFilter("*"))
async def start_limit_add(callback: types.CallbackQuery, state: FSMContext):
    # Повний список категорій з KEYWORDS_MAP
    categories = [
        "Продукти 🛒", "Транспорт 🚕", "Відпочинок ☕", 
        "Дім/Побут 🏠", "Здоров'я 💊", "Техніка 💻",
        "Одяг та взуття 👕", "Краса та догляд ✨", 
        "Донати та подарунки 🎁", "Тварини 🐾"
    ]
    
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat, callback_data=f"setlcat_{cat}")
    builder.adjust(2) # Кнопки у два стовпчики для зручності
    
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
    
    db.set_limit(message.from_user.id, category, amount)
    
    success_text = (
        f"✅ <b>Ліміт встановлено!</b>\n"
        "<code>" + "—" * 20 + "</code>\n"
        f"📌 <b>Категорія:</b> {category}\n"
        f"💰 <b>Сума:</b> <code>{amount:.2f} грн/міс</code>\n\n"
        "<i>Бот автоматично попередить вас при наближенні до цієї суми.</i>"
    )
    await message.answer(success_text, reply_markup=main_menu(), parse_mode="HTML")
    await state.clear()

# --- ВИДАЛЕННЯ ЛІМІТУ ---
@router.callback_query(F.data == "limit_delete_menu", StateFilter("*"))
async def show_delete_limits_list(callback: types.CallbackQuery):
    limits = db.get_limits(callback.from_user.id)
    if not limits:
        await callback.answer("У вас немає лімітів для видалення.")
        return

    builder = InlineKeyboardBuilder()
    for category, amount in limits:
        builder.button(text=f"Видалити {category} ❌", callback_data=f"limitdel_{category}")
    
    builder.button(text="Назад 🔙", callback_data="limit_back")
    builder.adjust(1)
    
    text = (
        "🗑 <b>ВИДАЛЕННЯ ЛІМІТУ</b>\n\n"
        "Оберіть категорію, яку хочете прибрати з моніторингу:"
    )
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("limitdel_"), StateFilter("*"))
async def execute_limit_deletion(callback: types.CallbackQuery):
    category = callback.data.split("_")[1]
    db.delete_limit(callback.from_user.id, category)
    
    text = f"✅ <b>Успішно:</b> Ліміт для '{category}' видалено."
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "limit_back", StateFilter("*"))
async def limit_back(callback: types.CallbackQuery):
    await render_limits_menu(callback)
    await callback.answer()