import asyncio
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from src.loader import bot
from src.database.engine import async_session
from src.database.models import User
from sqlalchemy import select

async def send_broadcast(message_text: str):
    async with async_session() as session:
        # 1. Отримуємо список усіх користувачів
        result = await session.execute(select(User.telegram_id))
        users = result.scalars().all()
        
        print(f"📢 Починаю розсилку для {len(users)} користувачів...")
        
        count = 0
        for user_id in users:
            try:
                await bot.send_message(user_id, message_text, parse_mode="HTML")
                count += 1
                # Невелика пауза, щоб Telegram не заблокував за спам
                await asyncio.sleep(0.05) 
            except TelegramForbiddenError:
                print(f"🚫 Користувач {user_id} заблокував бота.")
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                await bot.send_message(user_id, message_text)
            except Exception as e:
                print(f"❌ Помилка для {user_id}: {e}")

        print(f"✅ Розсилка завершена! Отримали: {count} осіб.")

if __name__ == "__main__":
    text = (
        "🚀 <b>ВЕЛИКЕ ОНОВЛЕННЯ!</b>\n\n"
        "Ваш фінансовий помічник переїхав на новий потужний двигун <b>PostgreSQL</b>! 🐘\n"
        "Тепер бот працює швидше, а статистика стала темною та красивою. 🌑\n\n"
        "Спробуйте натиснути <b>Статистика 📊</b> прямо зараз!"
    )
    asyncio.run(send_broadcast(text))