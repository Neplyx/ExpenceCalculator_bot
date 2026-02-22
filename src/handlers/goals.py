from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter
from datetime import datetime

# Імпорт компонентів з нової структури
from src.utils.states import GoalStates
from src.database import requests as rq
from src.utils.formatter import get_progress_bar
from src.keyboards.main_menu import main_menu_kb

router = Router()

@router.message(F.text == "Цілі 🎯", StateFilter(None))
async def show_goals_menu(message: types.Message):
    # Отримуємо список об'єктів Goal з Postgres
    goals = await rq.get_goals(message.from_user.id)
    builder = InlineKeyboardBuilder()
    
    if not goals:
        # ТЕКСТ БЕЗ ЗМІН
        text = (
            "🎯 <b>ФІНАНСОВІ ЦІЛІ</b>\n"
            "<code>" + "—" * 20 + "</code>\n\n"
            "У вас ще немає активних цілей. Час поставити нову фінансову мету та почати шлях до мрії! 🚀"
        )
        builder.button(text="Створити першу ціль 🚀", callback_data="goal_add")
    else:
        # ТЕКСТ БЕЗ ЗМІН
        text = "🏆 <b>ТВОЇ ФІНАНСОВІ ВЕРШИНИ</b>\n"
        text += "<code>" + "—" * 20 + "</code>\n\n"
        
        for goal in goals:
            progress = get_progress_bar(goal.current_amount, goal.target_amount)
            left = max(goal.target_amount - goal.current_amount, 0)
            
            goal_info = (
                f"📌 <b>{goal.name.upper()}</b>\n{progress}\n"
                f"💰 <code>{goal.current_amount:.2f} / {goal.target_amount:.2f} грн</code>\n"
            )
            
            if goal.deadline and left > 0:
                try:
                    # Deadline тепер є об'єктом date або datetime в моделі
                    days_left = (goal.deadline - datetime.now().date()).days
                    if days_left > 0:
                        weeks = max(days_left / 7, 1)
                        per_week = left / weeks
                        goal_info += f"📅 Дедлайн: <code>{goal.deadline}</code>\n💡 План: <b><code>{per_week:.2f} грн/тиж</code></b>\n"
                    else:
                        goal_info += "⚠️ <b>Термін виконання вийшов!</b>\n"
                except:
                    goal_info += f"📅 Дедлайн: <code>{goal.deadline}</code>\n"
            
            if left <= 0:
                goal_info += "✅ <b>ЦІЛЬ ДОСЯГНУТА!</b>\n"
            
            text += goal_info + "\n"
            builder.button(text=f"Відкласти на {goal.name} 💸", callback_data=f"goal_topup_{goal.name}")
        
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
    # ТЕКСТ БЕЗ ЗМІН
    await callback.message.answer(
        f"💰 <b>ПОПОВНЕННЯ:</b> '{goal_name.upper()}'\n\nВведіть суму, яку ви сьогодні відклали:", 
        parse_mode="HTML"
    )
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
    
    # Оновлюємо в Postgres
    await rq.update_goal_savings(message.from_user.id, goal_name, amount)
    
    # Перевіряємо досягнення цілі
    updated_goals = await rq.get_goals(message.from_user.id)
    for goal in updated_goals:
        if goal.name == goal_name and goal.current_amount >= goal.target_amount:
            # ТЕКСТ СВЯТКУВАННЯ БЕЗ ЗМІН
            celebration = (
                f"🎊 <b>ВІТАЮ, {message.from_user.first_name.upper()}!</b> 🎊\n"
                "<code>" + "—" * 20 + "</code>\n\n"
                f"🥳 Ти щойно досягнув цілі: <b>'{goal_name}'</b>!\n"
                "<i>Твоя дисципліна дала результат. Насолоджуйся перемогою!</i> 🎆"
            )
            await message.answer(celebration, parse_mode="HTML", reply_markup=main_menu_kb())
            await state.clear()
            return

    await message.answer(
        f"✅ <b>Додано <code>{amount:.2f} грн</code>!</b>\nКрок за кроком до мрії! 🚀", 
        reply_markup=main_menu_kb(), 
        parse_mode="HTML"
    )
    await state.clear()

# --- СТВОРЕННЯ НОВОЇ ЦІЛІ ---

@router.callback_query(F.data == "goal_add", StateFilter("*"))
async def start_goal_add(callback: types.CallbackQuery, state: FSMContext):
    # ТЕКСТ БЕЗ ЗМІН
    text = (
        "✍️ <b>Крок 1: Назва цілі</b>\n\n"
        "Напишіть, на що саме ви збираєте кошти (наприклад: <code>Новий ноутбук</code>):"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(GoalStates.entering_name)

@router.message(GoalStates.entering_name)
async def process_goal_name(message: types.Message, state: FSMContext):
    await state.update_data(goal_name=message.text)
    # ТЕКСТ БЕЗ ЗМІН
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
    
    # ТЕКСТ БЕЗ ЗМІН
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
    
    # Записуємо в Postgres
    await rq.add_goal(message.from_user.id, data['goal_name'], data['goal_target'], deadline)
    
    # ТЕКСТ БЕЗ ЗМІН
    success_text = (
        "✨ <b>Ціль успішно створена!</b>\n\n"
        f"📌 <b>Назва:</b> {data['goal_name']}\n"
        f"💰 <b>Мета:</b> {data['goal_target']:.2f} грн\n"
        f"📅 <b>Термін:</b> {deadline or 'Не встановлено'}"
    )
    await message.answer(success_text, parse_mode="HTML", reply_markup=main_menu_kb())
    await state.clear()

# --- ВИДАЛЕННЯ ЦІЛІ ---

@router.callback_query(F.data == "goal_delete_menu", StateFilter("*"))
async def goal_delete_list(callback: types.CallbackQuery):
    goals = await rq.get_goals(callback.from_user.id)
    builder = InlineKeyboardBuilder()
    
    for goal in goals:
        builder.button(text=f"Видалити {goal.name} ❌", callback_data=f"goaldel_{goal.name}")
    
    builder.adjust(1)
    await callback.message.edit_text(
        "🗑 <b>Оберіть ціль для видалення:</b>", 
        reply_markup=builder.as_markup(), 
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("goaldel_"), StateFilter("*"))
async def execute_goal_del(callback: types.CallbackQuery):
    name = callback.data.split("_")[1]
    # Видаляємо з Postgres
    await rq.delete_goal(callback.from_user.id, name)
    
    await callback.message.edit_text(f"🗑 <b>Ціль '{name}' успішно видалена.</b>", parse_mode="HTML")
    await callback.answer()