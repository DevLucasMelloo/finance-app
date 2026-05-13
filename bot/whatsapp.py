import os
import httpx

EVOLUTION_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_KEY = os.getenv("EVOLUTION_API_KEY", "")
INSTANCE = os.getenv("EVOLUTION_INSTANCE", "finance-bot")


def send_text(remote_jid: str, text: str) -> None:
    url = f"{EVOLUTION_URL}/message/sendText/{INSTANCE}"
    headers = {"apikey": EVOLUTION_KEY, "Content-Type": "application/json"}
    payload = {"number": remote_jid, "text": text}
    try:
        with httpx.Client(timeout=10) as client:
            client.post(url, json=payload, headers=headers)
    except Exception as exc:
        print(f"[whatsapp] send_text error: {exc}")
