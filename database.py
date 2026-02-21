import sqlite3
from datetime import datetime, timedelta

def init_db():
    with sqlite3.connect("expenses.db") as connection:
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, category TEXT, date TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS limits (user_id INTEGER, category TEXT, amount REAL, PRIMARY KEY (user_id, category))""")
        # Базова структура таблиці з урахуванням дедлайну
        cursor.execute("""CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT, target_amount REAL, current_amount REAL DEFAULT 0, deadline TEXT)""")
        
        # БЛОК МІГРАЦІЇ: Додаємо колонку deadline, якщо її немає
        try:
            cursor.execute("ALTER TABLE goals ADD COLUMN deadline TEXT")
        except sqlite3.OperationalError:
            pass
            
        cursor.execute("""CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER, 
            name TEXT, 
            amount REAL, 
            next_date TEXT, 
            period TEXT DEFAULT 'monthly')""")
        connection.commit()

def add_expense(user_id, amount, category, date):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)", (user_id, amount, category, date))

def show_expenses(user_id):
    with sqlite3.connect("expenses.db") as conn:
        res = conn.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (user_id,)).fetchone()
        return res[0] or 0

def history_expense(user_id):
    """Повертає список останніх 5 витрат для подальшого форматування"""
    with sqlite3.connect("expenses.db") as conn:
        # Повертаємо чисті дані, а не текст
        return conn.execute(
            "SELECT amount, category, date FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 5", 
            (user_id,)
        ).fetchall()

def daily_expense(user_id, target_date):
    with sqlite3.connect("expenses.db") as conn:
        res = conn.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date = ?", (user_id, target_date)).fetchone()
        return res[0] or 0

def get_last_expense(user_id):
    with sqlite3.connect("expenses.db") as conn:
        return conn.execute("SELECT amount, category FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()

def delete_last_expense(user_id):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("DELETE FROM expenses WHERE id = (SELECT MAX(id) FROM expenses WHERE user_id = ?)", (user_id,))

def get_category_data(user_id):
    with sqlite3.connect("expenses.db") as conn:
        return conn.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category", (user_id,)).fetchall()

def set_limit(user_id, category, amount):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("INSERT OR REPLACE INTO limits (user_id, category, amount) VALUES (?, ?, ?)", (user_id, category, amount))

def get_limit(user_id, category):
    with sqlite3.connect("expenses.db") as conn:
        res = conn.execute("SELECT amount FROM limits WHERE user_id = ? AND category = ?", (user_id, category)).fetchone()
        return res[0] if res else None

def get_limits(user_id):
    with sqlite3.connect("expenses.db") as conn:
        return conn.execute("SELECT category, amount FROM limits WHERE user_id = ?", (user_id,)).fetchall()

def delete_limit(user_id, category):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("DELETE FROM limits WHERE user_id = ? AND category = ?", (user_id, category))

def add_goal(user_id, name, amount):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("INSERT INTO goals (user_id, name, target_amount) VALUES (?, ?, ?)", (user_id, name, amount))

def get_goals(user_id):
    with sqlite3.connect("expenses.db") as conn:
        return conn.execute("SELECT name, target_amount FROM goals WHERE user_id = ?", (user_id,)).fetchall()

def delete_goal(user_id, name):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("DELETE FROM goals WHERE user_id = ? AND name = ?", (user_id, name))

def get_month_sum_by_category(user_id, category, start):
    with sqlite3.connect("expenses.db") as conn:
        res = conn.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND category = ? AND date >= ?", (user_id, category, start)).fetchone()
        return res[0] or 0

def get_all_users():
    with sqlite3.connect("expenses.db") as conn:
        return [r[0] for r in conn.execute("SELECT DISTINCT user_id FROM expenses").fetchall()]

def get_weekly_summary(user_id):
    with sqlite3.connect("expenses.db") as conn:
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        total = conn.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date >= ?", (user_id, week_ago)).fetchone()[0] or 0
        top = conn.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = ? AND date >= ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1", (user_id, week_ago)).fetchone()
        return total, top

# database.py

def get_expenses_period(user_id, days=None, start_of_month=False):
    with sqlite3.connect("expenses.db") as conn:
        if start_of_month:
            # Початок поточного місяця
            date_str = datetime.now().strftime("%Y-%m-01")
        else:
            # Кількість днів тому від сьогодні
            date_str = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        res = conn.execute(
            "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date >= ?", 
            (user_id, date_str)
        ).fetchone()
        return res[0] or 0
    
def add_goal(user_id, name, amount, deadline=None):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("INSERT INTO goals (user_id, name, target_amount, current_amount, deadline) VALUES (?, ?, ?, 0, ?)", 
                     (user_id, name, amount, deadline))
        
def update_goal_savings(user_id, name, amount):
    """Додає кошти до існуючої цілі"""
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("UPDATE goals SET current_amount = current_amount + ? WHERE user_id = ? AND name = ?", (amount, user_id, name))

def get_goals(user_id):
    with sqlite3.connect("expenses.db") as conn:
        return conn.execute("SELECT name, target_amount, current_amount, deadline FROM goals WHERE user_id = ?", (user_id,)).fetchall()

def add_subscription(user_id, name, amount, next_date):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("INSERT INTO subscriptions (user_id, name, amount, next_date) VALUES (?, ?, ?, ?)", 
                     (user_id, name, amount, next_date))

def get_subscriptions(user_id):
    with sqlite3.connect("expenses.db") as conn:
        return conn.execute("SELECT id, name, amount, next_date FROM subscriptions WHERE user_id = ?", (user_id,)).fetchall()

def delete_subscription(sub_id):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))

def add_subscription(user_id, name, amount, next_date):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("INSERT INTO subscriptions (user_id, name, amount, next_date) VALUES (?, ?, ?, ?)", 
                     (user_id, name, amount, next_date))

def get_subscriptions(user_id):
    with sqlite3.connect("expenses.db") as conn:
        return conn.execute("SELECT id, name, amount, next_date FROM subscriptions WHERE user_id = ?", (user_id,)).fetchall()

def delete_subscription(sub_id):
    with sqlite3.connect("expenses.db") as conn:
        conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))

def get_subs_by_date(date_str):
    """Шукає всі підписки, дата оплати яких збігається з поточною"""
    with sqlite3.connect("expenses.db") as conn:
        return conn.execute(
            "SELECT user_id, name, amount FROM subscriptions WHERE next_date = ?", 
            (date_str,)
        ).fetchall()
    
def get_subs_by_date(date_str):
    """Отримує список підписок, термін яких настав сьогодні."""
    with sqlite3.connect("expenses.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, name, amount FROM subscriptions WHERE next_date = ?", 
            (date_str,)
        )
        return cursor.fetchall()

def update_subscription_date(sub_id, current_date_str):
    """Переносить дату наступного списання на один місяць вперед."""
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
    # Приблизне додавання 30 днів для наступного місяця
    next_date = (current_date + timedelta(days=30)).strftime("%Y-%m-%d")
    
    with sqlite3.connect("expenses.db") as conn:
        conn.execute(
            "UPDATE subscriptions SET next_date = ? WHERE id = ?", 
            (next_date, sub_id)
        )