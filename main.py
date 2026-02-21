import asyncio
import logging
from loader import dp, bot, scheduler
import database as db
# Додаємо subscriptions у імпорт
from handlers import common, expenses, stats, goals, limits, subscriptions
from utils.scheduler_tasks import setup_scheduler

async def main():
    logging.basicConfig(level=logging.INFO)
    db.init_db()
    
    # 1. Специфічні команди (старт, допомога)
    dp.include_router(common.router)
    
    # 2. Модулі з FSM станами (ПЕРШОЧЕРГОВІ)
    # Вони мають бути вище, щоб перехоплювати текст під час анкет
    dp.include_router(subscriptions.router) # Додаємо сюди
    dp.include_router(goals.router)
    dp.include_router(limits.router)
    
    # 3. Модулі з кнопками та статистикою
    dp.include_router(stats.router)
    
    # 4. Обробка витрат - ЗАВЖДИ В САМОМУ КІНЦІ
    # Цей роутер спрацює, лише якщо повідомлення не підійшло під жоден стан вище
    dp.include_router(expenses.router)
    
    setup_scheduler()
    scheduler.start()
    
    logging.info("Бот запущений.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())