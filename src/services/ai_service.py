import re
import logging
from src.loader import client
from src.config import Config

class AIService:
    @staticmethod
    async def suggest_category(product_name: str) -> str:
        name_lower = product_name.lower().strip()
        
        # 1. Словникова перевірка (економить токени та час)
        for category, keywords in Config.KEYWORDS_MAP.items():
            for word in keywords:
                if re.search(rf'\b{word}\b', name_lower):
                    return category
        
        # 2. Пріоритетний список моделей з твого списку (від найшвидших)
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite", 
            "gemini-2.0-flash", 
            "gemini-2.0-flash-lite-preview-02-05",
            "gemini-1.5-flash", 
            "gemma-3-27b"
        ]

        prompt = (
            f"Визнач категорію для товару: '{product_name}'. "
            f"Обери ОДНУ назву ТІЛЬКИ з цього списку: {', '.join(Config.KEYWORDS_MAP.keys())}. "
            "Відповідай тільки назвою категорії без зайвих слів."
        )

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                category_name = response.text.strip()
                
                # Пошук повної назви з емодзі у твоєму KEYWORDS_MAP
                for full_cat in Config.KEYWORDS_MAP.keys():
                    if category_name.lower() in full_cat.lower():
                        return full_cat
                        
                # Якщо модель повернула текст без емодзі, але він співпадає за змістом
                return "Інше 📁"
            except Exception as e:
                logging.warning(f"Модель {model_name} недоступна: {e}")
                continue # Пробуємо наступну модель
        
        return "Інше 📁"