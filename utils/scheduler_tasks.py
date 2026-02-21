from loader import bot, scheduler  # Обов'язково додаємо імпорт scheduler
import database as db
import logging
from datetime import datetime

async def send_weekly_reports():
    """Функція для розсилки звітів усім користувачам"""
    users = db.get_all_users()
    for user_id in users:
        total, top_cat = db.get_weekly_summary(user_id)
        if total > 0:
            top_cat_text = f"{top_cat[0]} ({top_cat[1]} грн)" if top_cat else "немає"
            text = (
                "📊 <b>Твій щотижневий фінансовий звіт</b>\n\n"
                f"💰 Всього витрачено: {total} грн\n"
                f"🔝 Найбільша категорія: {top_cat_text}\n\n"
                "💡 Почни тиждень з планування!"
            )
            try:
                # Використовуємо HTML для сумісності з іншими частинами бота
                await bot.send_message(user_id, text, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Помилка надсилання звіту {user_id}: {e}")

def setup_scheduler():
    """Реєструє завдання в планувальнику"""
    # Додаємо завдання в чергу планувальника
    scheduler.add_job(
        send_weekly_reports, 
        "cron", 
        day_of_week="mon", 
        hour=9, 
        minute=0
    )

async def check_subscriptions_task():
    """Перевіряє підписки та надсилає сповіщення користувачам."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    subs_due = db.get_subs_by_date(today_str)
    
    for sub_id, user_id, name, amount in subs_due:
        text = (
            f"🔔 <b>ЧАС ОПЛАТИТИ ПІДПИСКУ!</b>\n"
            f"<code>" + "—" * 20 + "</code>\n\n"
            f"Сьогодні заплановане списання за: <b>{name}</b>\n"
            f"Сума до сплати: <code>{amount:.2f} грн</code>\n\n"
            f"<i>Перевірте баланс на картці, щоб сервіс не вимкнувся!</i> 💳"
        )
        try:
            # Надсилання повідомлення
            await bot.send_message(user_id, text, parse_mode="HTML")
            # Оновлення дати на наступний місяць
            db.update_subscription_date(sub_id, today_str)
        except Exception as e:
            logging.error(f"Помилка надсилання нагадування для {user_id}: {e}")

def setup_scheduler():
    """Налаштування розкладу виконання завдань."""
    # Запуск перевірки щодня о 09:00 ранку
    scheduler.add_job(check_subscriptions_task, "cron", hour=9, minute=0)