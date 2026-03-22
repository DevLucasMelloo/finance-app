import sqlite3
from infrastructure.database import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT entry_type, payment_method, nature FROM lancamentos;")
rows = cursor.fetchall()

print("DADOS DO BANCO:")
for row in rows:
    print(row)

conn.close()
