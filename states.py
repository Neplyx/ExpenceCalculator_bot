from aiogram.fsm.state import StatesGroup, State

class LimitStates(StatesGroup):
    choosing_category = State()
    entering_amount = State()

class GoalStates(StatesGroup):
    entering_name = State()
    entering_target = State()
    entering_deadline = State() # Новий стан для дати
    adding_savings = State()

class SubscriptionStates(StatesGroup):
    entering_name = State()
    entering_amount = State()
    entering_date = State()