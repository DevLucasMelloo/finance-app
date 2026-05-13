import sys
from pathlib import Path

# Garante que o root do projeto está no path para importar domain/repositories
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from bot import state as session_store
from bot.messages import MAIN_MENU, INVALID
from bot.flows import lancamento, investimento, saldo

_CANCEL_WORDS = {"cancelar", "sair", "menu"}


def handle(phone: str, text: str) -> str:
    sess = session_store.get(phone)
    step: str = sess["step"]
    data: dict = sess["data"]
    t = text.strip()

    # ── Comando global de cancelamento (exceto quando já no menu) ──
    if t.lower() in _CANCEL_WORDS and step != "MAIN_MENU":
        session_store.set_state(phone, "MAIN_MENU", {})
        return MAIN_MENU

    # ── Menu principal ──
    if step == "MAIN_MENU":
        if t == "1":
            session_store.set_state(phone, "LANC_MENU", {})
            return lancamento.MENU
        if t == "2":
            session_store.set_state(phone, "INV_MENU", {})
            return investimento.MENU
        if t == "3":
            session_store.set_state(phone, "MAIN_MENU", {})
            return saldo.get_saldo() + "\n\n" + MAIN_MENU
        return MAIN_MENU

    # ── Fluxo de lançamentos ──
    if step.startswith("LANC_"):
        reply, next_step, new_data = lancamento.handle(step, t, data)
        session_store.set_state(phone, next_step, new_data)
        if next_step == "MAIN_MENU":
            suffix = "\n\n" + MAIN_MENU if reply else MAIN_MENU
            return (reply + suffix).strip()
        return reply

    # ── Fluxo de investimentos ──
    if step.startswith("INV_"):
        reply, next_step, new_data = investimento.handle(step, t, data)
        session_store.set_state(phone, next_step, new_data)
        if next_step == "MAIN_MENU":
            suffix = "\n\n" + MAIN_MENU if reply else MAIN_MENU
            return (reply + suffix).strip()
        return reply

    # Fallback: reseta para o menu
    session_store.set_state(phone, "MAIN_MENU", {})
    return MAIN_MENU
