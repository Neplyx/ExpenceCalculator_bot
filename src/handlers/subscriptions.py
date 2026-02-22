from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter
from datetime import datetime

# Імпорт компонентів з нової структури
from src.utils.states import SubscriptionStates
from src.database import requests as rq
from src.keyboards.main_menu import main_menu_kb

router = Router()

@router.message(F.text == "Підписки 🔄", StateFilter(None))
async def show_subs_menu(message: types.Message):
    # Отримуємо список об'єктів Subscription з Postgres
    subs = await rq.get_subscriptions(message.from_user.id)
    builder = InlineKeyboardBuilder()
    
    # ТЕКСТ ТА ОФОРМЛЕННЯ БЕЗ ЗМІН
    text = "🔄 <b>РЕГУЛЯРНІ ПЛАТЕЖІ</b>\n"
    text += "<code>" + "—" * 20 + "</code>\n\n"
    
    if not subs:
        text += "<i>У вас ще немає регулярних платежів. Додайте Netflix або оплату за інтернет, щоб не забути про них!</i>\n\n"
    else:
        for sub in subs:
            # Використовуємо властивості об'єкта моделі
            text += f"▪️ <b>{sub.name}</b>\n💰 Сума: <code>{sub.amount:.2f} грн</code>\n🗓 Дата: <code>{sub.next_date}</code>\n\n"
            builder.button(text=f"Видалити {sub.name} 🗑", callback_data=f"subdel_{sub.id}")
            
    text += f"<code>" + "—" * 20 + "</code>"
    builder.button(text="Додати підписку ➕", callback_data="sub_add")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "sub_add", StateFilter(None))
async def sub_add_start(callback: types.CallbackQuery, state: FSMContext):
    # ТЕКСТ БЕЗ ЗМІН
    await callback.message.edit_text("🏷 <b>КРОК 1: НАЗВА</b>\n\nВведіть назву сервісу (наприклад: <code>Netflix</code>):", parse_mode="HTML")
    await state.set_state(SubscriptionStates.entering_name)

@router.message(SubscriptionStates.entering_name)
async def sub_add_name(message: types.Message, state: FSMContext):
    await state.update_data(sub_name=message.text)
    # ТЕКСТ БЕЗ ЗМІН
    await message.answer(f"💵 <b>КРОК 2: СУМА</b>\n\nСкільки коштує місячна підписка на <b>{message.text}</b>?", parse_mode="HTML")
    await state.set_state(SubscriptionStates.entering_amount)

@router.message(SubscriptionStates.entering_amount)
async def sub_add_amount(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '', 1).isdigit():
        # ТЕКСТ БЕЗ ЗМІН
        await message.answer("❌ <b>ПОМИЛКА:</b> Введіть коректне число (наприклад: <code>199.50</code>).", parse_mode="HTML")
        return
    await state.update_data(sub_amount=float(message.text))
    # ТЕКСТ БЕЗ ЗМІН
    await message.answer("📅 <b>КРОК 3: ДАТА ОПЛАТИ</b>\n\nВведіть дату наступного списання (<code>РРРР-ММ-ДД</code>):", parse_mode="HTML")
    await state.set_state(SubscriptionStates.entering_date)

@router.message(SubscriptionStates.entering_date)
async def sub_add_date(message: types.Message, state: FSMContext):
    try:
        # Перевірка формату дати залишається
        datetime.strptime(message.text, "%Y-%m-%d")
        data = await state.get_data()
        
        # Записуємо нову підписку в Postgres
        await rq.add_subscription(message.from_user.id, data['sub_name'], data['sub_amount'], message.text)
        
        # ТЕКСТ БЕЗ ЗМІН
        text = (
            "✅ <b>ПІДПИСКУ ДОДАНО!</b>\n"
            "<code>" + "—" * 20 + "</code>\n\n"
            f"📌 Сервіс: <b>{data['sub_name']}</b>\n"
            f"💰 Сума: <code>{data['sub_amount']:.2f} грн</code>\n"
            f"📅 Дата: <code>{message.text}</code>\n\n"
            "<i>Бот автоматично нагадає про оплату.</i>"
        )
        await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")
        await state.clear()
    except ValueError:
        # ТЕКСТ БЕЗ ЗМІН
        await message.answer("❌ <b>ПОМИЛКА:</b> Невірний формат. Використовуйте <code>РРРР-ММ-ДД</code>.", parse_mode="HTML")

@router.callback_query(F.data.startswith("subdel_"))
async def sub_delete(callback: types.CallbackQuery):
    sub_id = int(callback.data.split("_")[1])
    # Видаляємо з Postgres за ID
    await rq.delete_subscription(sub_id)
    # ТЕКСТ БЕЗ ЗМІН
    await callback.message.edit_text("✅ <b>УСПІШНО:</b> Підписку видалено.", parse_mode="HTML")
    await callback.answer()