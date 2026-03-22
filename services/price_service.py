import requests


class PriceService:
    URL = "https://api.coingecko.com/api/v3/simple/price"

    def __init__(self):
        self.last_data = {
            "BTC": {"brl": 0, "usd": 0},
            "ETH": {"brl": 0, "usd": 0},
            "XRP": {"brl": 0, "usd": 0},
            "USD": {"brl": 0}
        }

    def get_prices(self):
        try:
            params = {
                "ids": "bitcoin,ethereum,ripple,tether",
                "vs_currencies": "brl,usd"
            }

            response = requests.get(self.URL, params=params, timeout=5)
            data = response.json()

            result = {
                "BTC": data.get("bitcoin", {}),
                "ETH": data.get("ethereum", {}),
                "XRP": data.get("ripple", {}),
                "USD": data.get("tether", {})  # usamos USDT
            }

            # salva último valor válido
            self.last_data = result

            return result

        except Exception:
            # 🔥 retorna último valor válido (NUNCA quebra UI)
            return self.last_data

    def get_usd_brl(self):
        response = requests.get(
            self.URL,
            params={"ids": "tether", "vs_currencies": "brl"},
            timeout=5
        )

        data = response.json()
        return data.get("tether", {}).get("brl", 0)