# src/loader.py
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from google import genai
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# Ось тут ми кажемо: з модуля src.config імпортуй КЛАС Config
from src.config import Config

bot = Bot(token=Config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

client = genai.Client(api_key=Config.GEMINI_KEY)
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")