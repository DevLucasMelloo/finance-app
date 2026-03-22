import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent #add
#DB_PATH = Path("finance.db")
DB_PATH = BASE_DIR / "finance.db"#add
print("USANDO BANCO EM:", DB_PATH)



def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lancamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                amount REAL NOT NULL,
                entry_type TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                category TEXT NOT NULL,
                nature TEXT NOT NULL,
                description TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transferencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transfer_date TEXT NOT NULL,
                amount REAL NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                description TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS variacoes_investimento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_date TEXT NOT NULL,
                value_change REAL NOT NULL,
                description TEXT
            )
            """
        )

        conn.commit()
