import os
import sys
from pathlib import Path
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from bot import state, whatsapp
from bot.flows import handle

# Números permitidos (separados por vírgula no .env, ex: "5511999999999,5521988888888")
_raw = os.getenv("ALLOWED_NUMBERS", "")
ALLOWED = {n.strip() for n in _raw.split(",") if n.strip()}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.load()
    yield


app = FastAPI(title="Finance Bot", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"ok": False}

    event = body.get("event", "")
    if event != "messages.upsert":
        return {"ok": True}

    data = body.get("data", {})
    key = data.get("key", {})

    # Ignora mensagens enviadas pelo próprio bot
    if key.get("fromMe"):
        return {"ok": True}

    remote_jid: str = key.get("remoteJid", "")
    # Ignora grupos
    if "@g.us" in remote_jid:
        return {"ok": True}

    phone = remote_jid.replace("@s.whatsapp.net", "")

    # Segurança: só números autorizados
    if ALLOWED and phone not in ALLOWED:
        return {"ok": True}

    # Extrai texto da mensagem
    msg = data.get("message", {})
    text = (
        msg.get("conversation")
        or msg.get("extendedTextMessage", {}).get("text")
        or ""
    ).strip()

    if not text:
        return {"ok": True}

    reply = handle(phone, text)
    if reply:
        whatsapp.send_text(remote_jid, reply)

    return {"ok": True}
