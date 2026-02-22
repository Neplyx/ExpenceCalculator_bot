import sqlite3
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select

# Імпорт твоїх налаштувань та моделей
from src.database.engine import async_session, init_db
from src.database.models import User, Expense, Goal, Limit, Subscription

# Файл, який ти витягнув із сервера
OLD_DB_PATH = 'expenses (1).db' 

async def migrate():
    # 1. Створюємо таблиці в PostgreSQL, якщо їх ще немає
    await init_db()
    
    # 2. Відкриваємо стару базу SQLite
    try:
        sqlite_conn = sqlite3.connect(OLD_DB_PATH)
        cursor = sqlite_conn.cursor()
        
        # Перевіряємо, які таблиці реально існують
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [t[0] for t in cursor.fetchall()]
        print(f"✅ SQLite підключено. Таблиці: {existing_tables}")
    except Exception as e:
        print(f"❌ Помилка файлу {OLD_DB_PATH}: {e}")
        return

    async with async_session() as session:
        # --- КРОК 1: КОРИСТУВАЧІ ---
        # Збираємо унікальні ID з усіх таблиць
        print("🔍 Збір користувачів...")
        all_user_ids = set()
        for table in ['expenses', 'goals', 'limits', 'subscriptions']:
            if table in existing_tables:
                cursor.execute(f"SELECT DISTINCT user_id FROM {table}")
                all_user_ids.update(row[0] for row in cursor.fetchall())

        # Перевіряємо, хто вже є в Postgres
        existing_pg_users = await session.execute(select(User.telegram_id))
        existing_ids = set(existing_pg_users.scalars().all())

        for tg_id in all_user_ids:
            if tg_id not in existing_ids:
                session.add(User(telegram_id=tg_id, username=f"user_{tg_id}"))
        
        await session.commit()
        print(f"👤 Користувачі готові.")

        # --- КРОК 2: ВИТРАТИ ---
        if 'expenses' in existing_tables:
            cursor.execute("SELECT user_id, amount, category, date FROM expenses")
            for row in cursor.fetchall():
                try: d = datetime.strptime(row[3], "%Y-%m-%d").date()
                except: d = datetime.now().date()
                session.add(Expense(user_id=row[0], amount=row[1], category=row[2], date=d))
            print("💰 Витрати перенесені.")

        # --- КРОК 3: ЦІЛІ (виправлені назви колонок) ---
        if 'goals' in existing_tables:
            cursor.execute("SELECT user_id, name, target_amount, current_amount, deadline FROM goals")
            for row in cursor.fetchall():
                dl = None
                if row[4] and row[4] not in ['ні', 'None', '', 'NULL']:
                    try: dl = datetime.strptime(row[4], "%Y-%m-%d").date()
                    except: pass
                session.add(Goal(user_id=row[0], name=row[1], target_amount=row[2], current_amount=row[3], deadline=dl))
            print("🎯 Цілі перенесені.")

        # --- КРОК 4: ЛІМІТИ ТА ПІДПИСКИ ---
        if 'limits' in existing_tables:
            cursor.execute("SELECT user_id, category, amount FROM limits")
            for row in cursor.fetchall():
                await session.merge(Limit(user_id=row[0], category=row[1], amount=row[2]))
            print("📉 Ліміти перенесені.")

        if 'subscriptions' in existing_tables:
            cursor.execute("SELECT user_id, name, amount, next_date FROM subscriptions")
            for row in cursor.fetchall():
                try: nd = datetime.strptime(row[3], "%Y-%m-%d").date()
                except: nd = datetime.now().date()
                session.add(Subscription(user_id=row[0], name=row[1], amount=row[2], next_date=nd))
            print("🔄 Підписки перенесені.")

        await session.commit()
        print("\n🚀 МІГРАЦІЯ УСПІШНА!")

    sqlite_conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())