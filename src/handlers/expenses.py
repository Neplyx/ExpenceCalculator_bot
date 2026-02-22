from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

# Імпорт нового репозиторію та сервісів
from src.database import requests as rq
from src.services.ai_service import AIService
from src.keyboards.main_menu import main_menu_kb

router = Router()

# Твій оригінальний список кнопок меню
MENU_BUTTONS = [
    "Загальна сума 💰", "Історія витрат 📜", "Витрати 📊",
    "Видалити останню ❌", "Статистика 📊", "Курс валют 💵",
    "Цілі 🎯", "Ліміти 📉", "Підписки 🔄"
]

@router.message(F.text == "Загальна сума 💰", StateFilter(None))
async def cmd_total(message: types.Message):
    # Отримуємо суму з Postgres
    total = await rq.get_total_expenses(message.from_user.id)
    
    # ТЕКСТ ТА ОФОРМЛЕННЯ БЕЗ ЗМІН
    text = (
        "💰 <b>ЗАГАЛЬНИЙ БАЛАНС ВИТРАТ</b>\n"
        "<code>" + "—" * 20 + "</code>\n\n"
        f"Сума: <b><code>{total:.2f} грн</code></b>\n\n"
        f"<code>" + "—" * 20 + "</code>\n"
        "<i>Це загальна сума всіх твоїх записів у базі.</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "Історія витрат 📜", StateFilter(None))
async def cmd_history(message: types.Message):
    # Отримуємо чисті дані з Postgres
    history_data = await rq.get_expense_history(message.from_user.id)
    
    # ТЕКСТ ТА ОФОРМЛЕННЯ БЕЗ ЗМІН
    text = "📜 <b>ОСТАННІ ТРАНЗАКЦІЇ</b>\n"
    text += "<code>" + "—" * 20 + "</code>\n\n"
    
    if not history_data:
        text += "<i>Тут поки порожньо... Час щось купити!</i> 🛍"
    else:
        for expense in history_data:
            text += f"📅 {expense.date}\n└ <b>{expense.category}</b>: <code>{expense.amount:.2f} грн</code>\n\n"
    
    text += f"<code>" + "—" * 20 + "</code>"
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "Витрати 📊", StateFilter(None))
async def show_expenses_periods(message: types.Message):
    # ТЕКСТ ТА КНОПКИ БЕЗ ЗМІН
    builder = InlineKeyboardBuilder()
    builder.button(text="Сьогодні 📅", callback_data="exp_0")
    builder.button(text="Вчора ⏳", callback_data="exp_1")
    builder.button(text="Тиждень 🗓", callback_data="exp_7")
    builder.button(text="Місяць 🌙", callback_data="exp_month")
    builder.adjust(2)
    
    text = (
        "📊 <b>АНАЛІТИКА ПЕРІОДІВ</b>\n"
        "<code>" + "—" * 20 + "</code>\n\n"
        "За який проміжок часу ви хочете побачити детальний звіт?"
    )
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("exp_"), StateFilter(None))
async def process_period_selection(callback: types.CallbackQuery):
    period = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    # Використовуємо асинхронний метод з логікою періодів
    if period == "month":
        total = await rq.get_expenses_period(user_id, start_of_month=True)
        label = "ЦЕЙ МІСЯЦЬ 🌙"
    else:
        days = int(period)
        total = await rq.get_expenses_period(user_id, days=days)
        labels = {0: "СЬОГОДНІ 📅", 1: "ВЧОРА (ТА СЬОГОДНІ) ⏳", 7: "ОСТАННІЙ ТИЖДЕНЬ 🗓"}
        label = labels.get(days, "ОБРАНИЙ ПЕРІОД")

    # ТЕКСТ ТА ОФОРМЛЕННЯ БЕЗ ЗМІН
    text = (
        f"💳 <b>ЗВІТ ЗА {label}</b>\n"
        "<code>" + "—" * 20 + "</code>\n\n"
        f"Витрачено: <b><code>{total:.2f} грн</code></b>\n\n"
        "<code>" + "—" * 20 + "</code>"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

@router.message(F.text == "Видалити останню ❌", StateFilter(None))
async def confirm_delete(message: types.Message):
    # Отримуємо останню витрату з Postgres
    last = await rq.get_last_expense(message.from_user.id)
    if last:
        builder = InlineKeyboardBuilder()
        builder.button(text="Так, видалити ✅", callback_data="delete_yes")
        builder.button(text="Скасувати ❌", callback_data="delete_no")
        
        # ТЕКСТ ТА ОФОРМЛЕННЯ БЕЗ ЗМІН
        text = (
            "🗑 <b>ПІДТВЕРДЖЕННЯ ВИДАЛЕННЯ</b>\n"
            "<code>" + "—" * 20 + "</code>\n\n"
            f"Ви дійсно хочете видалити останній запис?\n"
            f"💰 Сума: <code>{last.amount:.2f} грн</code>\n"
            f"📁 Категорія: <b>{last.category}</b>"
        )
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.answer("❌ <b>ПОМИЛКА:</b> Твоя історія порожня.", parse_mode="HTML")

@router.callback_query(F.data.startswith("delete_"), StateFilter(None))
async def process_deletion(callback: types.CallbackQuery):
    if callback.data == "delete_yes":
        # Видаляємо з Postgres
        await rq.delete_last_expense(callback.from_user.id)
        await callback.message.edit_text("✅ <b>Успішно:</b> Запис назавжди видалено.", parse_mode="HTML")
    else:
        await callback.message.edit_text("🫡 <b>Скасовано:</b> Запис залишився в історії.", parse_mode="HTML")
    await callback.answer()

@router.message(F.text, ~F.text.in_(MENU_BUTTONS), ~F.text.startswith('/'), StateFilter(None))
async def process_expense(message: types.Message):
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2: return
        
        amount = float(parts[0].replace(',', '.')) 
        product_name = parts[1]
        
        status_msg = await message.answer("🔍 <b>Аналізую дані...</b>", parse_mode="HTML")
        
        # Використовуємо асинхронний AIService
        category = await AIService.suggest_category(product_name)
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Записуємо в Postgres
        await rq.add_expense(message.from_user.id, amount, category)
        
        # ТЕКСТ ТА ОФОРМЛЕННЯ "ЧЕКУ" БЕЗ ЗМІН
        final_text = (
            "🧾 <b>ФІНАНСОВИЙ ЧЕК</b>\n"
            "<code>" + "—" * 20 + "</code>\n\n"
            f"🔹 <b>Товар:</b> {product_name}\n"
            f"🔹 <b>Сума:</b> <code>{amount:.2f} грн</code>\n"
            f"🔹 <b>Категорія:</b> {category}\n\n"
            f"<code>" + "—" * 20 + "</code>\n"
            f"📅 <i>{date_str}</i>"
        )
        await status_msg.edit_text(final_text, parse_mode="HTML")

        # ПЕРЕВІРКА ЛІМІТІВ
        limit = await rq.get_limit(message.from_user.id, category)
        if limit:
            spent = await rq.get_monthly_category_sum(message.from_user.id, category)
            
            if spent >= limit:
                # ЧЕРВОНА ЗОНА (100%+)
                await message.answer(
                    f"🛑 <b>ЛІМІТ ПЕРЕВИЩЕНО!</b>\n"
                    f"<code>{ '—' * 20 }</code>\n" # ВИПРАВЛЕНО: множимо тільки тире
                    f"Категорія: {category}\n"
                    f"Витрачено: <b><code>{spent:.2f} / {limit:.2f} грн</code></b>", 
                    parse_mode="HTML"
                )
            elif spent >= limit * 0.75:
                # ЖОВТА ЗОНА (75%+)
                await message.answer(
                    f"⚠️ <b>УВАГА: НАБЛИЖЕННЯ ДО ЛІМІТУ!</b>\n"
                    f"<code>{ '—' * 20 }</code>\n" # ВИПРАВЛЕНО: множимо тільки тире
                    f"Ти вже використав понад <b>75%</b> бюджету на {category}.\n"
                    f"Залишилося: <code>{(limit - spent):.2f} грн</code>", 
                    parse_mode="HTML"
                )

    except ValueError: 
        await message.answer("❌ <b>ПОМИЛКА:</b> Введіть формат: <code>150 кава</code>", parse_mode="HTML")