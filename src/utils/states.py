from aiogram.fsm.state import State, StatesGroup

class GoalStates(StatesGroup):
    entering_name = State()
    entering_target = State()
    entering_deadline = State()
    adding_savings = State()

class LimitStates(StatesGroup):
    choosing_category = State()
    entering_amount = State()

class SubscriptionStates(StatesGroup):
    entering_name = State()
    entering_amount = State()
    entering_date = State()