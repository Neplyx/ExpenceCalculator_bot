from loader import bot, scheduler  # Обов'язково додаємо імпорт scheduler
import database as db
import logging
from datetime import datetime

async def send_weekly_reports():
    users = db.get_all_users()
    for user_id in users:
        total, top_cat = db.get_weekly_summary(user_id)
        if total > 0:
            top_cat_text = f"<b>{top_cat[0]}</b> (<code>{top_cat[1]:.2f} грн</code>)" if top_cat else "немає"
            text = (
                "📊 <b>ЩОТИЖНЕВИЙ ФІНАНСОВИЙ ЗВІТ</b>\n"
                "<code>" + "—" * 20 + "</code>\n\n"
                f"💰 Всього витрачено: <code>{total:.2f} грн</code>\n"
                f"🔝 Найбільша категорія: {top_cat_text}\n\n"
                f"<code>" + "—" * 20 + "</code>\n"
                "<i>Почни новий тиждень з планування!</i> 💡"
            )
            try:
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
    today_str = datetime.now().strftime("%Y-%m-%d")
    subs_due = db.get_subs_by_date(today_str)
    
    for sub_id, user_id, name, amount in subs_due:
        text = (
            "🔔 <b>ЧАС ОПЛАТИТИ ПІДПИСКУ!</b>\n"
            "<code>" + "—" * 20 + "</code>\n\n"
            f"📌 Заплановане списання: <b>{name}</b>\n"
            f"💰 Сума до сплати: <code>{amount:.2f} грн</code>\n\n"
            f"<code>" + "—" * 20 + "</code>\n"
            "<i>Перевірте баланс на картці!</i> 💳"
        )
        try:
            await bot.send_message(user_id, text, parse_mode="HTML")
            db.update_subscription_date(sub_id, today_str)
        except Exception as e:
            logging.error(f"Помилка надсилання нагадування для {user_id}: {e}")

def setup_scheduler():
    scheduler.add_job(send_weekly_reports, "cron", day_of_week="mon", hour=9, minute=0)
    scheduler.add_job(check_subscriptions_task, "cron", hour=9, minute=0)