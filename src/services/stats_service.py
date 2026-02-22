from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import FSInputFile
import matplotlib.pyplot as plt
import os

# Імпортуємо наші нові компоненти
from src.database import requests as rq
from src.services.currency_service import CurrencyService

router = Router()

# --- Константи для темної теми ---
DARK_BG_COLOR = '#121212'  # Дуже темний сірий (майже чорний) фон
TEXT_COLOR = '#FFFFFF'     # Білий текст

@router.message(F.text == "Статистика 📊", StateFilter(None))
@router.message(Command("stats"))
async def send_stats(message: types.Message):
    # Отримуємо дані для графіка з Postgres
    data = await rq.get_category_data(message.from_user.id)
    
    if not data:
        # ТЕКСТ БЕЗ ЗМІН
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

    # --- ПОЧАТОК НАЛАШТУВАННЯ ТЕМНОЇ ТЕМИ ---

    # 1. Встановлюємо базовий темний стиль
    plt.style.use('dark_background')

    # Створюємо фігуру та осі
    fig, ax = plt.subplots(figsize=(10, 7))

    # 2. Примусово встановлюємо колір фону для фігури та області графіка
    fig.patch.set_facecolor(DARK_BG_COLOR)
    ax.set_facecolor(DARK_BG_COLOR)

    # Використовуємо яскравішу палітру кольорів, яка краще виглядає на темному
    colors = plt.cm.Set2(range(len(categories)))
    
    # Малюємо діаграму
    wedges, texts, autotexts = ax.pie(
        amounts, labels=None, autopct='%1.1f%%', startangle=140, 
        colors=colors, pctdistance=0.85, explode=[0.05] * len(categories),
        # Гарантуємо, що відсотки на діаграмі білі
        textprops={'color': TEXT_COLOR, 'fontsize': 10, 'weight': 'bold'} 
    )

    # 3. ВАЖЛИВО: Змінюємо колір центрального кола з білого на темний фон
    centre_circle = plt.Circle((0,0), 0.70, fc=DARK_BG_COLOR)
    fig.gca().add_artist(centre_circle)
    
    # 4. Налаштовуємо заголовок (білий колір)
    plt.title(f"Розподіл витрат (Всього: {total_sum:.0f} грн)", fontsize=16, pad=20, color=TEXT_COLOR)
    
    # 5. Налаштовуємо легенду для темного фону
    legend = ax.legend(wedges, categories, title="Категорії", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    plt.setp(legend.get_title(), color=TEXT_COLOR) # Колір заголовка легенди
    frame = legend.get_frame()
    frame.set_facecolor(DARK_BG_COLOR) # Фон легенди
    frame.set_edgecolor('#404040')     # Тонка сіра рамка легенди
    for text in legend.get_texts():
        text.set_color(TEXT_COLOR)     # Колір тексту категорій у легенді
    
    image_path = f"stats_{message.from_user.id}.png"
    
    # 6. Зберігаємо зображення, явно вказуючи використовувати наш темний колір фону
    plt.savefig(image_path, bbox_inches='tight', dpi=150, facecolor=fig.get_facecolor())
    plt.close()

    # --- КІНЕЦЬ НАЛАШТУВАННЯ ТЕМНОЇ ТЕМИ ---

    # КАПШН БЕЗ ЗМІН
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
    # Використовуємо наш новий сервіс курсів
    rates = await CurrencyService.get_rates()
    if rates:
        # ТЕКСТ БЕЗ ЗМІН
        text = "🏦 <b>МОНІТОРИНГ ВАЛЮТ (MONOBANK)</b>\n"
        text += "<code>" + "—" * 20 + "</code>\n\n"
        
        curr_info = {
            "USD": ("🇺🇸", "USD"), 
            "EUR": ("🇪🇺", "EUR"), 
            "PLN": ("🇵🇱", "PLN"), 
            "GBP": ("🇬🇧", "GBP")
        }
        
        for code, (flag, name) in curr_info.items():
            if code in rates:
                info = rates[code]
                if info.get("is_cross"):
                    text += f"{flag} <b>{name}:</b> <code>{info['rate']:.2f} грн</code> (крос-курс)\n"
                else:
                    text += f"{flag} <b>{name}:</b> <code>{info['buy']:.2f} / {info['sell']:.2f} грн</code>\n"
        
        text += f"\n<code>" + "—" * 20 + "</code>\n🕒 <i>Дані оновлюються автоматично</i>"
        await message.answer(text, parse_mode="HTML")
    else:
        await message.answer("❌ <b>ПОМИЛКА:</b> Не вдалося отримати свіжий курс. Спробуйте пізніше.", parse_mode="HTML")