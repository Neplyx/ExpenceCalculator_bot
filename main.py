import asyncio
import logging
# Імпортуємо loader через повний шлях
from src.loader import dp, bot, scheduler
from src.database.engine import init_db

# Явні імпорти модулів
import src.handlers.common as common
import src.handlers.expenses as expenses
import src.services.stats_service as stats
import src.handlers.goals as goals
import src.handlers.limits as limits
import src.handlers.subscriptions as subscriptions
from src.utils.scheduler_tasks import setup_scheduler

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Ініціалізація бази
    await init_db()
    
    # Реєструємо роутери прямо з модулів
    dp.include_router(common.router)
    dp.include_router(subscriptions.router)
    dp.include_router(goals.router)
    dp.include_router(limits.router)
    dp.include_router(stats.router)
    dp.include_router(expenses.router)
    
    # Налаштування планувальника
    setup_scheduler()
    scheduler.start()
    
    logging.info("Бот на PostgreSQL успішно запущений.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот зупинений.")