def get_progress_bar(current: float, target: float, length: int = 10) -> str:
    """Створює візуальний рядок прогресу"""
    if target <= 0: return "░" * length
    
    percent = current / target
    filled_length = int(length * percent)
    
    # Обмежуємо довжину, якщо перевищено 100%
    if filled_length > length: filled_length = length
    if filled_length < 0: filled_length = 0
    
    bar = "🟩" * filled_length + "░" * (length - filled_length)
    
    # Додаємо вогник, якщо ціль досягнута або ліміт перевищено
    if percent >= 1.0:
        return bar + " 🔥"
        
    return bar + f" {int(percent * 100)}%"