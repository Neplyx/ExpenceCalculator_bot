from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter
from states import GoalStates
from datetime import datetime
import database as db
import math
from handlers.keyboard import main_menu 
from utils.formatter import get_progress_bar

router = Router()

@router.message(F.text == "Цілі 🎯", StateFilter(None))
async def show_goals_menu(message: types.Message):
    goals = db.get_goals(message.from_user.id)
    builder = InlineKeyboardBuilder()
    
    if not goals:
        text = (
            "🎯 <b>ФІНАНСОВІ ЦІЛІ</b>\n"
            "<code>" + "—" * 20 + "</code>\n\n"
            "У вас ще немає активних цілей. Час поставити нову фінансову мету та почати шлях до мрії! 🚀"
        )
        builder.button(text="Створити першу ціль 🚀", callback_data="goal_add")
    else:
        text = "🏆 <b>ТВОЇ ФІНАНСОВІ ВЕРШИНИ</b>\n"
        text += "<code>" + "—" * 20 + "</code>\n\n"
        
        for name, target, current, deadline in goals:
            progress = get_progress_bar(current, target)
            left = max(target - current, 0)
            
            goal_info = f"📌 <b>{name.upper()}</b>\n{progress}\n💰 <code>{current:.2f} / {target:.2f} грн</code>\n"
            
            if deadline and left > 0:
                try:
                    d_date = datetime.strptime(deadline, "%Y-%m-%d")
                    days_left = (d_date - datetime.now()).days
                    if days_left > 0:
                        weeks = max(days_left / 7, 1)
                        per_week = left / weeks
                        goal_info += f"📅 Дедлайн: <code>{deadline}</code>\n💡 План: <b><code>{per_week:.2f} грн/тиж</code></b>\n"
                    else:
                        goal_info += "⚠️ <b>Термін виконання вийшов!</b>\n"
                except:
                    goal_info += f"📅 Дедлайн: <code>{deadline}</code>\n"
            
            if left <= 0:
                goal_info += "✅ <b>ЦІЛЬ ДОСЯГНУТА!</b>\n"
            
            text += goal_info + "\n"
            builder.button(text=f"Відкласти на {name} 💸", callback_data=f"goal_topup_{name}")
        
        text += "<code>" + "—" * 20 + "</code>"
        builder.button(text="Додати нову ціль ➕", callback_data="goal_add")
        builder.button(text="Видалити ціль 🗑", callback_data="goal_delete_menu")
    
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

# --- ПОПОВНЕННЯ ЦІЛІ ---

@router.callback_query(F.data.startswith("goal_topup_"), StateFilter(None))
async def goal_topup_start(callback: types.CallbackQuery, state: FSMContext):
    goal_name = callback.data.split("_")[2]
    await state.update_data(active_goal=goal_name)
    await callback.message.answer(f"💰 <b>ПОПОВНЕННЯ:</b> '{goal_name.upper()}'\n\nВведіть суму, яку ви сьогодні відклали:", parse_mode="HTML")
    await state.set_state(GoalStates.adding_savings)
    await callback.answer()

@router.message(GoalStates.adding_savings)
async def goal_topup_finish(message: types.Message, state: FSMContext):
    if not message.text.replace('.', '', 1).isdigit():
        await message.answer("❌ <b>ПОМИЛКА:</b> Введіть число.")
        return
    
    amount = float(message.text)
    data = await state.get_data()
    goal_name = data['active_goal']
    db.update_goal_savings(message.from_user.id, goal_name, amount)
    
    # Логіка святкування досягнення
    updated_goals = db.get_goals(message.from_user.id)
    for name, target, current, _ in updated_goals:
        if name == goal_name and current >= target:
            celebration = (
                f"🎊 <b>ВІТАЮ, {message.from_user.first_name.upper()}!</b> 🎊\n"
                "<code>" + "—" * 20 + "</code>\n\n"
                f"🥳 Ти щойно досягнув цілі: <b>'{goal_name}'</b>!\n"
                "<i>Твоя дисципліна дала результат. Насолоджуйся перемогою!</i> 🎆"
            )
            await message.answer(celebration, parse_mode="HTML", reply_markup=main_menu())
            await state.clear()
            return

    await message.answer(f"✅ <b>Додано <code>{amount:.2f} грн</code>!</b>\nКрок за кроком до мрії! 🚀", reply_markup=main_menu(), parse_mode="HTML")
    await state.clear()
# --- СТВОРЕННЯ НОВОЇ ЦІЛІ ---

@router.callback_query(F.data == "goal_add", StateFilter("*"))
async def start_goal_add(callback: types.CallbackQuery, state: FSMContext):
    text = (
        "✍️ <b>Крок 1: Назва цілі</b>\n\n"
        "Напишіть, на що саме ви збираєте кошти (наприклад: <code>Новий ноутбук</code>):"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(GoalStates.entering_name)

@router.message(GoalStates.entering_name)
async def process_goal_name(message: types.Message, state: FSMContext):
    await state.update_data(goal_name=message.text)
    text = (
        f"💵 <b>Крок 2: Фінансова мета</b>\n\n"
        f"Яку суму потрібно зібрати для цілі <b>'{message.text}'</b>?"
    )
    await message.answer(text, parse_mode="HTML")
    await state.set_state(GoalStates.entering_target)

@router.message(GoalStates.entering_target)
async def process_goal_target(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ <b>Помилка:</b> Введіть ціле число.")
        return
    await state.update_data(goal_target=float(message.text))
    
    text = (
        "📅 <b>Крок 3: Дедлайн</b>\n\n"
        "Вкажіть дату, до якої хочете назбирати кошти у форматі <code>РРРР-ММ-ДД</code>.\n\n"
        "💡 <i>Якщо термін не важливий, просто напишіть 'ні'.</i>"
    )
    await message.answer(text, parse_mode="HTML")
    await state.set_state(GoalStates.entering_deadline)

@router.message(GoalStates.entering_deadline)
async def process_goal_deadline(message: types.Message, state: FSMContext):
    deadline = message.text if message.text.lower() != 'ні' else None
    data = await state.get_data()
    
    db.add_goal(message.from_user.id, data['goal_name'], data['goal_target'], deadline)
    
    success_text = (
        "✨ <b>Ціль успішно створена!</b>\n\n"
        f"📌 <b>Назва:</b> {data['goal_name']}\n"
        f"💰 <b>Мета:</b> {data['goal_target']:.2f} грн\n"
        f"📅 <b>Термін:</b> {deadline or 'Не встановлено'}"
    )
    await message.answer(success_text, parse_mode="HTML", reply_markup=main_menu())
    await state.clear()

# --- ВИДАЛЕННЯ ЦІЛІ ---

@router.callback_query(F.data == "goal_delete_menu", StateFilter("*"))
async def goal_delete_list(callback: types.CallbackQuery):
    goals = db.get_goals(callback.from_user.id)
    builder = InlineKeyboardBuilder()
    
    # ТУТ БУЛА ПОМИЛКА: тепер розпаковуємо всі 4 значення, які дає база
    for name, target, current, deadline in goals:
        builder.button(text=f"Видалити {name} ❌", callback_data=f"goaldel_{name}")
    
    builder.adjust(1)
    await callback.message.edit_text(
        "🗑 <b>Оберіть ціль для видалення:</b>", 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("goaldel_"), StateFilter("*"))
async def execute_goal_del(callback: types.CallbackQuery):
    name = callback.data.split("_")[1]
    db.delete_goal(callback.from_user.id, name)
    
    await callback.message.edit_text(f"🗑 <b>Ціль '{name}' успішно видалена.</b>", parse_mode="HTML")
    await callback.answer()