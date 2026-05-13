import requests

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "XRP": "ripple",
    "SOL": "solana",
}

TICKER_CARDS = ["BTC", "ETH", "XRP", "SOL"]


class PriceService:
    URL = "https://api.coingecko.com/api/v3/simple/price"

    def __init__(self):
        self.last_data = {t: {"brl": 0.0, "usd": 0.0} for t in TICKER_CARDS}
        self._usd_brl = 5.7  # fallback

    def get_prices(self) -> dict:
        try:
            ids = ",".join(COINGECKO_IDS.values())
            params = {"ids": ids, "vs_currencies": "brl,usd"}
            response = requests.get(self.URL, params=params, timeout=5)
            data = response.json()

            result = {}
            for ticker, cg_id in COINGECKO_IDS.items():
                entry = data.get(cg_id, {})
                result[ticker] = {
                    "brl": entry.get("brl", 0.0),
                    "usd": entry.get("usd", 0.0),
                }

            self.last_data = result
            return result

        except Exception:
            return self.last_data

    def get_current_price(self, ticker: str, currency: str = "brl") -> float:
        """Returns the current price for a single ticker in the given currency."""
        ticker = ticker.upper()
        if ticker not in COINGECKO_IDS:
            return 0.0
        prices = self.get_prices()
        return prices.get(ticker, {}).get(currency, 0.0)

    def get_usd_brl(self) -> float:
        try:
            response = requests.get(
                self.URL,
                params={"ids": "tether", "vs_currencies": "brl"},
                timeout=5,
            )
            val = response.json().get("tether", {}).get("brl", self._usd_brl)
            self._usd_brl = val
            return val
        except Exception:
            return self._usd_brl
