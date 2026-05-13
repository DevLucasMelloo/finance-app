import json
from pathlib import Path

_SESSIONS_FILE = Path(__file__).parent / "sessions.json"

_sessions: dict[str, dict] = {}


def load():
    global _sessions
    if _SESSIONS_FILE.exists():
        try:
            _sessions = json.loads(_SESSIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            _sessions = {}


def get(phone: str) -> dict:
    return _sessions.get(phone, {"step": "MAIN_MENU", "data": {}})


def set_state(phone: str, step: str, data: dict | None = None):
    _sessions[phone] = {"step": step, "data": data or {}}
    _persist()


def reset(phone: str):
    _sessions.pop(phone, None)
    _persist()


def _persist():
    try:
        _SESSIONS_FILE.write_text(
            json.dumps(_sessions, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass
