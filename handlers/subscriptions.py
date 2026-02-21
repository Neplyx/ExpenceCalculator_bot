from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter
from states import SubscriptionStates
from handlers.keyboard import main_menu
import database as db
from datetime import datetime

router = Router()

@router.message(F.text == "Підписки 🔄", StateFilter(None))
async def show_subs_menu(message: types.Message):
    subs = db.get_subscriptions(message.from_user.id)
    builder = InlineKeyboardBuilder()
    
    text = "🔄 <b>РЕГУЛЯРНІ ПЛАТЕЖІ</b>\n"
    text += "<code>" + "—" * 20 + "</code>\n\n"
    
    if not subs:
        text += "<i>У вас ще немає регулярних платежів. Додайте Netflix або оплату за інтернет, щоб не забути про них!</i>\n\n"
    else:
        for sub_id, name, amt, date in subs:
            text += f"▪️ <b>{name}</b>\n💰 Сума: <code>{amt:.2f} грн</code>\n🗓 Дата: <code>{date}</code>\n\n"
            builder.button(text=f"Видалити {name} 🗑", callback_data=f"subdel_{sub_id}")
            
    text += f"<code>" + "—" * 20 + "</code>"
    builder.button(text="Додати підписку ➕", callback_data="sub_add")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

@router.callback_query(F.data == "sub_add", StateFilter(None))
async def sub_add_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🏷 <b>КРОК 1: НАЗВА</b>\n\nВведіть назву сервісу (наприклад: <code>Netflix</code>):", parse_mode="HTML")
    await state.set_state(SubscriptionStates.entering_name)

@router.message(SubscriptionStates.entering_name)
async def sub_add_name(message: types.Message, state: FSMContext):
    await state.update_data(sub_name=message.text)
    await message.answer(f"💵 <b>КРОК 2: СУМА</b>\n\nСкільки коштує місячна підписка на <b>{message.text}</b>?", parse_mode="HTML")
    await state.set_state(SubscriptionStates.entering_amount)

@router.message(SubscriptionStates.entering_amount)
async def sub_add_amount(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '', 1).isdigit():
        await message.answer("❌ <b>ПОМИЛКА:</b> Введіть коректне число (наприклад: <code>199.50</code>).", parse_mode="HTML")
        return
    await state.update_data(sub_amount=float(message.text))
    await message.answer("📅 <b>КРОК 3: ДАТА ОПЛАТИ</b>\n\nВведіть дату наступного списання (<code>РРРР-ММ-ДД</code>):", parse_mode="HTML")
    await state.set_state(SubscriptionStates.entering_date)

@router.message(SubscriptionStates.entering_date)
async def sub_add_date(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%Y-%m-%d")
        data = await state.get_data()
        db.add_subscription(message.from_user.id, data['sub_name'], data['sub_amount'], message.text)
        
        text = (
            "✅ <b>ПІДПИСКУ ДОДАНО!</b>\n"
            "<code>" + "—" * 20 + "</code>\n\n"
            f"📌 Сервіс: <b>{data['sub_name']}</b>\n"
            f"💰 Сума: <code>{data['sub_amount']:.2f} грн</code>\n"
            f"📅 Дата: <code>{message.text}</code>\n\n"
            "<i>Бот автоматично нагадає про оплату.</i>"
        )
        await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")
        await state.clear()
    except ValueError:
        await message.answer("❌ <b>ПОМИЛКА:</b> Невірний формат. Використовуйте <code>РРРР-ММ-ДД</code>.", parse_mode="HTML")

@router.callback_query(F.data.startswith("subdel_"))
async def sub_delete(callback: types.CallbackQuery):
    sub_id = callback.data.split("_")[1]
    db.delete_subscription(sub_id)
    await callback.message.edit_text("✅ <b>УСПІШНО:</b> Підписку видалено.", parse_mode="HTML")
    await callback.answer()