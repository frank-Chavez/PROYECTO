import sqlite3


def conection():
    conn = sqlite3.connect("database.db", timeout=10)  # tu archivo .db
    conn.row_factory = sqlite3.Row  # para acceder a las columnas por nombre
    return conn