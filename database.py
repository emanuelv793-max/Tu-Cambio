import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('historial.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cantidad REAL NOT NULL,
            moneda_origen TEXT NOT NULL,
            moneda_destino TEXT NOT NULL,
            resultado TEXT NOT NULL,
            tasa REAL NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def guardar_conversion(cantidad, moneda_origen, moneda_destino, resultado, tasa):
    conn = sqlite3.connect('historial.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO historial (cantidad, moneda_origen, moneda_destino, resultado, tasa)
        VALUES (?, ?, ?, ?, ?)
    ''', (cantidad, moneda_origen, moneda_destino, resultado, tasa))
    conn.commit()
    conn.close()

def obtener_historial(limite=5):
    conn = sqlite3.connect('historial.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM historial ORDER BY fecha DESC LIMIT ?', (limite,))
    historial = cursor.fetchall()
    conn.close()
    return historial
