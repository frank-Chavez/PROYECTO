import sqlite3
import unicodedata


# ----------------------------------------Ignorar acentos al buscar en cualquier modulo----------------------------------------
def remove_acentos(text):
    if text is None:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


# ----------------------------------------Coneccion a la base de  datos----------------------------------------
def conection():
    conn = sqlite3.connect("database.db", timeout=10)
    conn.row_factory = sqlite3.Row
    conn.create_function("remove_acentos", 1, remove_acentos)
    return conn
