from src.loader import bot, scheduler
from src.database import requests as rq
from datetime import datetime

async def check_subscriptions():
    """Перевіряє підписки, які потрібно оплатити сьогодні"""
    subs_due = await rq.get_subs_due_today()
    for sub in subs_due:
        try:
            text = (
                f"🔔 <b>НАГАДУВАННЯ ПРО ОПЛАТУ</b>\n"
                f"<code>" + "—" * 20 + "</code>\n\n"
                f"Сьогодні час оплатити підписку: <b>{sub.name}</b>\n"
                f"💰 Сума до сплати: <code>{sub.amount:.2f} грн</code>\n\n"
                f"<i>Після оплати дата автоматично перенесеться на місяць вперед.</i>"
            )
            await bot.send_message(sub.user_id, text, parse_mode="HTML")
            # Оновлюємо дату на наступний місяць
            await rq.update_subscription_date(sub.id)
        except Exception as e:
            print(f"Помилка відправки нагадування для {sub.user_id}: {e}")

async def send_weekly_report():
    """Відправляє підсумок витрат за тиждень усім користувачам"""
    user_ids = await rq.get_all_users()
    for user_id in user_ids:
        try:
            total, top_cat = await rq.get_weekly_summary(user_id)
            if total > 0:
                text = (
                    f"📊 <b>ТИЖНЕВИЙ ЗВІТ</b>\n"
                    f"<code>" + "—" * 20 + "</code>\n\n"
                    f"За останні 7 днів ви витратили: <b><code>{total:.2f} грн</code></b>\n"
                )
                if top_cat:
                    text += f"🔝 Головна категорія: <b>{top_cat[0]}</b> (<code>{top_cat[1]:.2f} грн</code>)\n"
                
                text += f"\n<i>Продовжуйте контролювати свої фінанси!</i> 🚀"
                await bot.send_message(user_id, text, parse_mode="HTML")
        except Exception as e:
            print(f"Помилка тижневого звіту для {user_id}: {e}")

def setup_scheduler():
    """Налаштовує графік виконання завдань"""
    # Перевірка підписок щодня о 10:00
    scheduler.add_job(check_subscriptions, "cron", hour=10, minute=0)
    # Тижневий звіт щопонеділка о 09:00
    scheduler.add_job(send_weekly_report, "cron", day_of_week="mon", hour=9, minute=0)