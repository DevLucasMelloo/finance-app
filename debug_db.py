import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "finance.db"
conn = sqlite3.connect(DB_PATH)

rows = conn.execute(
    "SELECT entry_type, payment_method FROM lancamentos"
).fetchall()

print("DADOS REAIS DO BANCO:")
for r in rows:
    print(r)
