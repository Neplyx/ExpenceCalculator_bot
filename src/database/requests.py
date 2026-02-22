from src.database.engine import async_session
from src.database.models import User, Expense, Goal, Limit, Subscription
from sqlalchemy import select, update, delete, func, desc
from datetime import datetime, timedelta

# --- КОРИСТУВАЧІ ---

async def add_user(tg_id: int, username: str | None):
    """Реєструє нового користувача, якщо його ще немає в базі"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == tg_id))
        if not user:
            session.add(User(telegram_id=tg_id, username=username))
            await session.commit()

async def get_all_users():
    """Повертає список ID всіх користувачів для розсилок"""
    async with async_session() as session:
        result = await session.execute(select(User.telegram_id))
        return [row[0] for row in result.all()]

# --- ВИТРАТИ ---

async def add_expense(tg_id: int, amount: float, category: str):
    """Додає новий запис про витрату"""
    async with async_session() as session:
        session.add(Expense(user_id=tg_id, amount=amount, category=category))
        await session.commit()

async def get_total_expenses(tg_id: int):
    """Повертає загальну суму всіх витрат користувача"""
    async with async_session() as session:
        result = await session.execute(
            select(func.sum(Expense.amount)).where(Expense.user_id == tg_id)
        )
        return result.scalar() or 0.0

async def get_expense_history(tg_id: int, limit: int = 5):
    """Повертає список останніх витрат"""
    async with async_session() as session:
        result = await session.execute(
            select(Expense)
            .where(Expense.user_id == tg_id)
            .order_by(desc(Expense.id))
            .limit(limit)
        )
        return result.scalars().all()

async def get_last_expense(tg_id: int):
    """Отримує останню витрату для перевірки перед видаленням"""
    async with async_session() as session:
        result = await session.execute(
            select(Expense)
            .where(Expense.user_id == tg_id)
            .order_by(desc(Expense.id))
            .limit(1)
        )
        return result.scalar()

async def delete_last_expense(tg_id: int):
    """Видаляє останню транзакцію користувача"""
    async with async_session() as session:
        last_expense = await get_last_expense(tg_id)
        if last_expense:
            await session.delete(last_expense)
            await session.commit()

async def get_category_data(tg_id: int):
    """Групує витрати по категоріях для статистики"""
    async with async_session() as session:
        result = await session.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(Expense.user_id == tg_id)
            .group_by(Expense.category)
        )
        return result.all()

async def get_expenses_period(tg_id: int, days: int = None, start_of_month: bool = False):
    """Розраховує витрати за вказаний період (сьогодні, тиждень, місяць)"""
    async with async_session() as session:
        if start_of_month:
            start_date = datetime.now().replace(day=1).date()
        else:
            start_date = (datetime.now() - timedelta(days=days)).date()
        
        result = await session.execute(
            select(func.sum(Expense.amount))
            .where(Expense.user_id == tg_id, Expense.date >= start_date)
        )
        return result.scalar() or 0.0

async def get_weekly_summary(tg_id: int):
    """Отримує суму та топ-категорію за останні 7 днів"""
    async with async_session() as session:
        week_ago = (datetime.now() - timedelta(days=7)).date()
        
        total = await session.scalar(
            select(func.sum(Expense.amount))
            .where(Expense.user_id == tg_id, Expense.date >= week_ago)
        ) or 0.0
        
        top = (await session.execute(
            select(Expense.category, func.sum(Expense.amount))
            .where(Expense.user_id == tg_id, Expense.date >= week_ago)
            .group_by(Expense.category)
            .order_by(desc(func.sum(Expense.amount)))
            .limit(1)
        )).fetchone()
        
        return total, top

# --- ЛІМІТИ ---

async def set_limit(tg_id: int, category: str, amount: float):
    """Встановлює або оновлює місячний ліміт"""
    async with async_session() as session:
        limit = await session.scalar(
            select(Limit).where(Limit.user_id == tg_id, Limit.category == category)
        )
        if limit:
            limit.amount = amount
        else:
            session.add(Limit(user_id=tg_id, category=category, amount=amount))
        await session.commit()

async def get_limit(tg_id: int, category: str):
    """Повертає значення ліміту для конкретної категорії"""
    async with async_session() as session:
        return await session.scalar(
            select(Limit.amount).where(Limit.user_id == tg_id, Limit.category == category)
        )

async def get_limits(tg_id: int):
    """Повертає всі ліміти користувача"""
    async with async_session() as session:
        result = await session.execute(select(Limit).where(Limit.user_id == tg_id))
        return result.scalars().all()

async def delete_limit(tg_id: int, category: str):
    """Видаляє ліміт для категорії"""
    async with async_session() as session:
        await session.execute(
            delete(Limit).where(Limit.user_id == tg_id, Limit.category == category)
        )
        await session.commit()

# --- ЦІЛІ ---

async def add_goal(tg_id: int, name: str, target: float, deadline: str | None):
    """Створює нову фінансову ціль"""
    async with async_session() as session:
        # Конвертуємо дедлайн у Date, якщо він переданий
        d_obj = datetime.strptime(deadline, "%Y-%m-%d").date() if deadline and deadline != "ні" else None
        session.add(Goal(user_id=tg_id, name=name, target_amount=target, deadline=d_obj))
        await session.commit()

async def get_goals(tg_id: int):
    """Повертає список всіх цілей користувача"""
    async with async_session() as session:
        result = await session.execute(select(Goal).where(Goal.user_id == tg_id))
        return result.scalars().all()

async def update_goal_savings(tg_id: int, name: str, amount: float):
    """Додає кошти до прогресу цілі"""
    async with async_session() as session:
        goal = await session.scalar(
            select(Goal).where(Goal.user_id == tg_id, Goal.name == name)
        )
        if goal:
            goal.current_amount += amount
            await session.commit()

async def delete_goal(tg_id: int, name: str):
    """Видаляє ціль за назвою"""
    async with async_session() as session:
        await session.execute(
            delete(Goal).where(Goal.user_id == tg_id, Goal.name == name)
        )
        await session.commit()

# --- ПІДПИСКИ ---

async def add_subscription(tg_id: int, name: str, amount: float, next_date: str):
    """Додає нову підписку"""
    async with async_session() as session:
        d_obj = datetime.strptime(next_date, "%Y-%m-%d").date()
        session.add(Subscription(user_id=tg_id, name=name, amount=amount, next_date=d_obj))
        await session.commit()

async def get_subscriptions(tg_id: int):
    """Повертає всі активні підписки користувача"""
    async with async_session() as session:
        result = await session.execute(select(Subscription).where(Subscription.user_id == tg_id))
        return result.scalars().all()

async def delete_subscription(sub_id: int):
    """Видаляє підписку за її ID"""
    async with async_session() as session:
        await session.execute(delete(Subscription).where(Subscription.id == sub_id))
        await session.commit()

async def get_subs_due_today():
    """Знаходить всі підписки, термін оплати яких сьогодні"""
    async with async_session() as session:
        today = datetime.now().date()
        result = await session.execute(select(Subscription).where(Subscription.next_date == today))
        return result.scalars().all()

async def update_subscription_date(sub_id: int):
    """Переносить дату наступної оплати на 30 днів вперед"""
    async with async_session() as session:
        sub = await session.get(Subscription, sub_id)
        if sub:
            sub.next_date += timedelta(days=30)
            await session.commit()

async def get_monthly_category_sum(tg_id: int, category: str):
    """Розраховує суму витрат по категорії за поточний місяць"""
    async with async_session() as session:
        start_of_month = datetime.now().replace(day=1).date()
        result = await session.execute(
            select(func.sum(Expense.amount))
            .where(
                Expense.user_id == tg_id, 
                Expense.category == category, 
                Expense.date >= start_of_month
            )
        )
        return result.scalar() or 0.0