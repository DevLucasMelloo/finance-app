import os
from datetime import date
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_connection():
    """Returns a thin _Conn wrapper around a psycopg2 connection."""
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não definida. Crie um arquivo .env com:\n"
            "DATABASE_URL=postgresql://postgres:[senha]@[host]:5432/postgres"
        )
    raw = psycopg2.connect(DATABASE_URL)
    return _Conn(raw)


def to_date(v) -> date:
    """Accepts both datetime.date and ISO-string (compatibility helper)."""
    if v is None:
        return None
    if hasattr(v, "year"):
        return v
    return date.fromisoformat(str(v))


class _Conn:
    """
    Thin adapter so existing repositories (written for sqlite3) work with
    psycopg2 without changing call sites:
        conn.execute(sql, params).fetchall()
        conn.commit()
    """

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql: str, params=()):
        cur = self._raw.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params if params else None)
        return cur

    def cursor(self):
        return self._raw.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def commit(self):
        self._raw.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        if exc_type:
            self._raw.rollback()
        else:
            self._raw.commit()
        self._raw.close()


def initialize_database() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lancamentos (
                id            BIGSERIAL PRIMARY KEY,
                entry_date    DATE        NOT NULL,
                amount        FLOAT       NOT NULL,
                entry_type    TEXT        NOT NULL,
                payment_method TEXT       NOT NULL,
                category      TEXT        NOT NULL,
                nature        TEXT        NOT NULL,
                description   TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS transferencias (
                id             BIGSERIAL PRIMARY KEY,
                transfer_date  DATE  NOT NULL,
                amount         FLOAT NOT NULL,
                origin         TEXT  NOT NULL,
                destination    TEXT  NOT NULL,
                description    TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS variacoes_investimento (
                id             BIGSERIAL PRIMARY KEY,
                reference_date DATE  NOT NULL,
                value_change   FLOAT NOT NULL,
                description    TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id              BIGSERIAL PRIMARY KEY,
                asset           TEXT  NOT NULL,
                asset_type      TEXT  NOT NULL DEFAULT 'OUTRO',
                total_quantity  FLOAT NOT NULL DEFAULT 0,
                avg_price       FLOAT NOT NULL DEFAULT 0,
                total_invested  FLOAT NOT NULL DEFAULT 0,
                broker          TEXT,
                origin_account  TEXT  NOT NULL DEFAULT 'CAIXA',
                is_open         INTEGER NOT NULL DEFAULT 1,
                created_at      DATE,
                closed_at       DATE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS buys (
                id           BIGSERIAL PRIMARY KEY,
                position_id  BIGINT NOT NULL REFERENCES positions(id),
                quantity     FLOAT  NOT NULL,
                price        FLOAT  NOT NULL,
                total_value  FLOAT  NOT NULL,
                broker       TEXT,
                date         DATE   NOT NULL,
                lancamento_id BIGINT REFERENCES lancamentos(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sells (
                id           BIGSERIAL PRIMARY KEY,
                position_id  BIGINT NOT NULL REFERENCES positions(id),
                quantity     FLOAT  NOT NULL,
                price        FLOAT  NOT NULL,
                total_value  FLOAT  NOT NULL,
                profit       FLOAT,
                date         DATE   NOT NULL,
                lancamento_id BIGINT REFERENCES lancamentos(id)
            )
        """)
