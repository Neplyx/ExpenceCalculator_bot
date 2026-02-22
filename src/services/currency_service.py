import requests
import time

class CurrencyService:
    _cached_rates = None
    _last_update = 0

    @classmethod
    async def get_rates(cls):
        # Кешування на 10 хвилин
        if cls._cached_rates and (time.time() - cls._last_update < 600):
            return cls._cached_rates

        try:
            response = requests.get("https://api.monobank.ua/bank/currency", timeout=10)
            if response.status_code == 200:
                data = response.json()
                codes = {840: "USD", 978: "EUR", 985: "PLN", 826: "GBP"}
                rates = {}
                
                for item in data:
                    if item["currencyCodeA"] in codes and item["currencyCodeB"] == 980:
                        name = codes[item["currencyCodeA"]]
                        if "rateBuy" in item and "rateSell" in item:
                            rates[name] = {"buy": item["rateBuy"], "sell": item["rateSell"], "is_cross": False}
                        elif "rateCross" in item:
                            rates[name] = {"rate": item["rateCross"], "is_cross": True}
                
                if rates:
                    cls._cached_rates, cls._last_update = rates, time.time()
                    return rates
        except Exception as e:
            print(f"Помилка валют: {e}")
        return cls._cached_rates