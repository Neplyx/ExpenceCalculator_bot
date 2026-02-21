from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
from utils.ai_helper import ai_suggest_category
import database as db

router = Router()

MENU_BUTTONS = [
    "Загальна сума 💰", "Історія витрат 📜", "Витрати 📊",
    "Видалити останню ❌", "Статистика 📊", "Курс валют 💵",
    "Цілі 🎯", "Ліміти 📉", "Підписки 🔄"
]

@router.message(
    F.text, 
    ~F.text.in_(MENU_BUTTONS), 
    StateFilter(None) # Обробляти тільки якщо користувач не в анкеті
)

@router.message(F.text == "Загальна сума 💰", StateFilter("*"))
async def cmd_total(message: types.Message):
    total = db.show_expenses(message.from_user.id)
    text = (
        "💰 <b>ЗАГАЛЬНИЙ БАЛАНС ВИТРАТ</b>\n"
        "<code>" + "—" * 20 + "</code>\n"
        f"Сума: <b>{total:.2f} грн</b>\n\n"
        "<i>Це загальна сума всіх твоїх записів у базі.</i>"
    )
    await message.answer(text, parse_mode="HTML")

# --- ІСТОРІЯ ВИТРАТ (СТИЛІЗОВАНА ЯК ВИПИСКА) ---
@router.message(F.text == "Історія витрат 📜")
@router.message(Command("history"))
async def cmd_history(message: types.Message):
    history_data = db.history_expense(message.from_user.id)
    
    text = "📜 <b>ОСТАННІ ТРАНЗАКЦІЇ:</b>\n"
    text += "<code>" + "—" * 20 + "</code>\n\n"
    
    if not history_data or "нічого не знайшов" in str(history_data).lower():
        text += "<i>Тут поки порожньо... Час щось купити!</i> 🛍"
    else:
        # Припускаємо, що база повертає форматований текст або ми його обробляємо
        text += f"<code>{history_data}</code>"
    
    text += "\n\n<code>" + "—" * 20 + "</code>"
    await message.answer(text, parse_mode="HTML")

# --- ВИБІР ПЕРІОДУ ВИТРАТ ---
@router.message(F.text == "Витрати 📊", StateFilter("*"))
async def show_expenses_periods(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Сьогодні 📅", callback_data="exp_0")
    builder.button(text="Вчора ⏳", callback_data="exp_1")
    builder.button(text="Тиждень 🗓", callback_data="exp_7")
    builder.button(text="Місяць 🌙", callback_data="exp_month")
    builder.adjust(2)
    
    text = (
        "📊 <b>АНАЛІТИКА ПЕРІОДІВ</b>\n\n"
        "За який проміжок часу ви хочете побачити детальний звіт?"
    )
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("exp_"), StateFilter("*"))
async def process_period_selection(callback: types.CallbackQuery):
    period = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    if period == "month":
        total = db.get_expenses_period(user_id, start_of_month=True)
        label = "ЦЕЙ МІСЯЦЬ 🌙"
    else:
        days = int(period)
        total = db.get_expenses_period(user_id, days=days)
        labels = {0: "СЬОГОДНІ 📅", 1: "ВЧОРА (ТА СЬОГОДНІ) ⏳", 7: "ОСТАННІЙ ТИЖДЕНЬ 🗓"}
        label = labels.get(days, "ОБРАНИЙ ПЕРІОД")

    text = (
        f"💳 <b>ЗВІТ ЗА {label}</b>\n"
        "<code>" + "—" * 20 + "</code>\n"
        f"Витрачено: <b>{total:.2f} грн</b>\n"
        "<code>" + "—" * 20 + "</code>"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

# --- ВИДАЛЕННЯ ---
@router.message(F.text == "Видалити останню ❌")
async def confirm_delete(message: types.Message):
    last = db.get_last_expense(message.from_user.id)
    if last:
        amount, category = last
        builder = InlineKeyboardBuilder()
        builder.button(text="Так, видалити ✅", callback_data="delete_yes")
        builder.button(text="Скасувати ❌", callback_data="delete_no")
        
        text = (
            "🗑 <b>ПІДТВЕРДЖЕННЯ ВИДАЛЕННЯ</b>\n\n"
            f"Ви дійсно хочете видалити останній запис?\n"
            f"💰 Сума: <code>{amount:.2f} грн</code>\n"
            f"📁 Категорія: <b>{category}</b>"
        )
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.answer("❌ <b>Помилка:</b> Нічого видаляти. Ваша історія порожня.", parse_mode="HTML")

@router.callback_query(F.data.startswith("delete_"))
async def process_deletion(callback: types.CallbackQuery):
    if callback.data == "delete_yes":
        db.delete_last_expense(callback.from_user.id)
        await callback.message.edit_text("✅ <b>Успішно:</b> Запис назавжди видалено з бази.", parse_mode="HTML")
    else:
        await callback.message.edit_text("🫡 <b>Скасовано:</b> Запис залишився в історії.", parse_mode="HTML")
    await callback.answer()

# --- ДОДАВАННЯ ВИТРАТИ (ЧЕК) ---
@router.message(F.text, ~F.text.in_(MENU_BUTTONS), ~F.text.startswith('/'), StateFilter("*"))
async def process_expense(message: types.Message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2: return
        
        amount = float(parts[0]) 
        product_name = parts[1]
        
        status_msg = await message.answer("🔍 <b>Визначаю категорію...</b>", parse_mode="HTML")
        category = await ai_suggest_category(product_name)
        date = datetime.now().strftime("%Y-%m-%d")
        
        db.add_expense(message.from_user.id, amount, category, date)
        
        final_text = (
            "<b>🧾 ФІНАНСОВИЙ ЧЕК</b>\n"
            "<code>" + "-"*20 + "</code>\n"
            f"<b>ТОВАР:</b>  {product_name}\n"
            f"<b>СУМА:</b>   {amount:.2f} грн\n"
            f"<b>КАТ:</b>    {category}\n"
            "<code>" + "-"*20 + "</code>\n"
            f"📅 {date}"
        )
        await status_msg.edit_text(final_text, parse_mode="HTML")

        # --- ЛОГІКА ПЕРЕВІРКИ ЛІМІТУ ---
        limit = db.get_limit(message.from_user.id, category)
        if limit:
            month_start = datetime.now().strftime("%Y-%m-01")
            current_month_sum = db.get_month_sum_by_category(message.from_user.id, category, month_start)
            
            if current_month_sum >= limit:
                warning_text = (
                    f"⚠️ <b>УВАГА! ЛІМІТ ПЕРЕВИЩЕНО!</b>\n"
                    "<code>" + "—" * 20 + "</code>\n"
                    f"Категорія: <b>{category}</b>\n"
                    f"Витрачено: <code>{current_month_sum:.2f}</code> грн\n"
                    f"Ліміт: <code>{limit:.2f}</code> грн\n"
                    "<code>" + "—" * 20 + "</code>\n"
                    "<i>Час зупинитися!</i> 🛑"
                )
                await message.answer(warning_text, parse_mode="HTML")
            
            elif current_month_sum >= limit * 0.75:
                warning_text = (
                    f"ℹ️ <b>ПОПЕРЕДЖЕННЯ (75%+)</b>\n"
                    "<code>" + "—" * 20 + "</code>\n"
                    f"Категорія: <b>{category}</b>\n"
                    f"Використано: <code>{current_month_sum:.2f} / {limit:.2f} грн</code>\n\n"
                    "<i>Будьте обачні з бюджетом!</i> 🧐"
                )
                await message.answer(warning_text, parse_mode="HTML")

    except ValueError: 
        await message.answer("❌ <b>Помилка:</b> Будь ласка, введіть коректну суму (наприклад: 123.45)", parse_mode="HTML")
        