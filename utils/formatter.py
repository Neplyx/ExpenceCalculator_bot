# utils/formatter.py

def get_progress_bar(current, limit):
    """Генерує візуальну шкалу прогресу в стилі Premium"""
    if limit <= 0:
        return "<code>⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜</code> 0%"
    
    percent = min(int((current / limit) * 100), 100)
    filled_length = int(percent // 10)
    
    # Використовуємо червоний квадрат, якщо ліміт перевищено, інакше зелений
    char = "🟥" if current >= limit else "🟩"
    
    # Формуємо рядок прогресу
    bar = char * filled_length + "⬜" * (10 - filled_length)
    
    # Огортаємо в code для моноширинності
    return f"<code>{bar}</code> {percent}%"