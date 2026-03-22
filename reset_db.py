import os
from infrastructure.database import DB_PATH, initialize_database

if DB_PATH.exists():
    os.remove(DB_PATH)
    print("Banco antigo removido")

initialize_database()
print("Banco recriado com sucesso")
