import requests
import time

cached_rates = None
last_update_time = 0

def get_currency_rates():
    global cached_rates, last_update_time
    # Кешування на 10 хвилин (600 секунд)
    if cached_rates and (time.time() - last_update_time < 600):
        return cached_rates

    try:
        response = requests.get("https://api.monobank.ua/bank/currency", timeout=10)
        if response.status_code == 200:
            data = response.json()
            # ISO коди: 840 (USD), 978 (EUR), 985 (PLN), 826 (GBP), 980 (UAH)
            codes = {840: "USD", 978: "EUR", 985: "PLN", 826: "GBP"}
            rates = {}
            
            for item in data:
                # Перевіряємо, чи це потрібна нам валюта відносно гривні
                if item["currencyCodeA"] in codes and item["currencyCodeB"] == 980:
                    currency_name = codes[item["currencyCodeA"]]
                    # Деякі валюти можуть мати прямий курс (rateCross), інші - купівля/продаж
                    buy = item.get("rateBuy") or item.get("rateCross")
                    sell = item.get("rateSell") or item.get("rateCross")
                    
                    if buy and sell:
                        rates[currency_name] = (float(buy), float(sell))
            
            # Якщо ми знайшли хоча б основні валюти, оновлюємо кеш
            if rates:
                cached_rates, last_update_time = rates, time.time()
                return rates
                
    except Exception as e:
        print(f"Помилка валют: {e}")
    
    return cached_rates