from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import FSInputFile
import matplotlib.pyplot as plt
import os
import database as db
from utils.currency_helper import get_currency_rates 

router = Router()

@router.message(F.text == "Статистика 📊", StateFilter(None))
@router.message(Command("stats"))
async def send_stats(message: types.Message):
    data = db.get_category_data(message.from_user.id)
    
    if not data:
        text = (
            "📊 <b>АНАЛІТИКА ВИТРАТ</b>\n"
            "<code>" + "—" * 20 + "</code>\n\n"
            "<i>У вас ще немає записів для формування звіту. Додайте свою першу витрату!</i> 🛍"
        )
        await message.answer(text, parse_mode="HTML")
        return

    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]
    total_sum = sum(amounts)

    plt.style.use('ggplot') 
    fig, ax = plt.subplots(figsize=(10, 7))
    colors = plt.cm.Paired(range(len(categories)))
    wedges, texts, autotexts = ax.pie(
        amounts, labels=None, autopct='%1.1f%%', startangle=140, 
        colors=colors, pctdistance=0.85, explode=[0.05] * len(categories) 
    )
    centre_circle = plt.Circle((0,0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)
    plt.title(f"Розподіл витрат (Всього: {total_sum:.0f} грн)", fontsize=16, pad=20)
    ax.legend(wedges, categories, title="Категорії", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    image_path = f"stats_{message.from_user.id}.png"
    plt.savefig(image_path, bbox_inches='tight', dpi=150)
    plt.close()

    caption = (
        "📊 <b>ГЛОБАЛЬНА АНАЛІТИКА</b>\n"
        "<code>" + "—" * 20 + "</code>\n\n"
        f"💰 Загальна сума: <code>{total_sum:.2f} грн</code>\n"
        f"🗂 Задіяно категорій: <code>{len(categories)}</code>\n\n"
        "<b>Топ витрат:</b>\n"
    )
    
    for cat, amt in zip(categories, amounts):
        percent = (amt / total_sum) * 100
        caption += f"🔹 {cat}: <code>{amt:.2f} грн</code> (<b>{percent:.1f}%</b>)\n"
    
    caption += f"\n<code>" + "—" * 20 + "</code>"

    photo = FSInputFile(image_path)
    await message.answer_photo(photo, caption=caption, parse_mode="HTML")
    if os.path.exists(image_path): os.remove(image_path)


@router.message(F.text == "Курс валют 💵", StateFilter(None))
async def show_rates(message: types.Message):
    rates = get_currency_rates()
    if rates:
        text = "🏦 <b>МОНІТОРИНГ ВАЛЮТ (MONOBANK)</b>\n"
        text += "<code>" + "—" * 20 + "</code>\n\n"
        
        curr_info = {"USD": ("🇺🇸", "USD"), "EUR": ("🇪🇺", "EUR"), "PLN": ("🇵🇱", "PLN"), "GBP": ("🇬🇧", "GBP")}
        for code, (flag, name) in curr_info.items():
            if code in rates:
                buy, sell = rates[code]
                text += f"{flag} <b>{name}:</b> <code>{buy:.2f} / {sell:.2f} грн</code>\n"
        
        text += f"\n<code>" + "—" * 20 + "</code>\n🕒 <i>Дані оновлюються автоматично</i>"
        await message.answer(text, parse_mode="HTML")
    else:
        await message.answer("❌ <b>ПОМИЛКА:</b> Не вдалося отримати свіжий курс. Спробуйте пізніше.", parse_mode="HTML")