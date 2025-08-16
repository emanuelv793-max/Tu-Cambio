from flask import Flask, render_template, request, jsonify
import requests
import os
import logging
from logging.handlers import RotatingFileHandler
from functools import lru_cache
from database import init_db, guardar_conversion, obtener_historial

# Configuración inicial
app = Flask(__name__)
init_db()  # Crear la base de datos al iniciar

# Configurar logging con rotación
if not app.logger.handlers:
    os.makedirs('.', exist_ok=True)
    handler = RotatingFileHandler('app.log', maxBytes=1_000_000, backupCount=3)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

# Lista de monedas (ampliada)
MONEDAS = [
    {"codigo": "EUR", "nombre": "Euro", "bandera": "https://flagcdn.com/eu.svg"},
    {"codigo": "USD", "nombre": "Dólar estadounidense", "bandera": "https://flagcdn.com/us.svg"},
    {"codigo": "VES", "nombre": "Bolívar venezolano", "bandera": "https://flagcdn.com/ve.svg"},
    {"codigo": "PYG", "nombre": "Guaraní paraguayo", "bandera": "https://flagcdn.com/py.svg"},
    {"codigo": "ARS", "nombre": "Peso argentino", "bandera": "https://flagcdn.com/ar.svg"},
    {"codigo": "MXN", "nombre": "Peso mexicano", "bandera": "https://flagcdn.com/mx.svg"},
    {"codigo": "CLP", "nombre": "Peso chileno", "bandera": "https://flagcdn.com/cl.svg"},
    {"codigo": "COP", "nombre": "Peso colombiano", "bandera": "https://flagcdn.com/co.svg"},
    {"codigo": "BRL", "nombre": "Real brasileño", "bandera": "https://flagcdn.com/br.svg"},
    {"codigo": "GBP", "nombre": "Libra esterlina", "bandera": "https://flagcdn.com/gb.svg"},
    {"codigo": "JPY", "nombre": "Yen japonés", "bandera": "https://flagcdn.com/jp.svg"},
    {"codigo": "CAD", "nombre": "Dólar canadiense", "bandera": "https://flagcdn.com/ca.svg"},
    {"codigo": "AUD", "nombre": "Dólar australiano", "bandera": "https://flagcdn.com/au.svg"},
    {"codigo": "CHF", "nombre": "Franco suizo", "bandera": "https://flagcdn.com/ch.svg"},
    {"codigo": "CNY", "nombre": "Yuan chino", "bandera": "https://flagcdn.com/cn.svg"},
    {"codigo": "SEK", "nombre": "Corona sueca", "bandera": "https://flagcdn.com/se.svg"},
]

# Índice para búsqueda rápida de metadatos de moneda
MONEDA_IDX = {m["codigo"]: m for m in MONEDAS}

# Cache simple para tasas de cambio (evita llamadas repetidas a la API durante el ciclo de proceso)
@lru_cache(maxsize=64)
def obtener_tasa(base: str, destino: str) -> float:
    try:
        resp = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=5)
        resp.raise_for_status()
        datos = resp.json()
        return float(datos["rates"][destino])
    except (requests.exceptions.RequestException, KeyError, ValueError) as e:
        app.logger.error(f"Error al obtener tasa {base}->{destino}: {e}")
        # Tasas por defecto (backup básico)
        tasas_defecto = {
            ("EUR", "USD"): 1.09, ("USD", "EUR"): 0.92,
            ("VES", "PYG"): 0.0045, ("PYG", "VES"): 220.00,
            ("ARS", "USD"): 0.0011, ("MXN", "USD"): 0.05,
            ("CLP", "USD"): 0.0011, ("COP", "USD"): 0.00025,
            ("BRL", "USD"): 0.19, ("GBP", "USD"): 1.25,
            ("JPY", "USD"): 0.0064, ("CAD", "USD"): 0.73,
            ("AUD", "USD"): 0.66, ("CHF", "USD"): 1.11,
            ("CNY", "USD"): 0.14, ("SEK", "USD"): 0.095,
        }
        return float(tasas_defecto.get((base, destino), 1.0))


def _formatear_resultado(cod_destino: str, valor: float) -> str:
    # Sin decimales para monedas con denominaciones muy pequeñas
    if cod_destino in {"PYG", "VES"}:
        return f"{valor:,.0f}"
    return f"{valor:,.2f}"


@app.route("/")
def index():
    # Obtener últimos elementos del historial y enriquecer para la plantilla
    filas = obtener_historial(5) or []
    historial = []
    for fila in filas:
        # Estructura esperada del SELECT *: (id, cantidad, moneda_origen, moneda_destino, resultado, tasa, fecha)
        try:
            _, cantidad, cod_origen, cod_destino, resultado_str, tasa_val, _ = fila
        except Exception:
            # Si cambia el orden de columnas, evitar romper la vista
            continue
        m_origen = MONEDA_IDX.get(cod_origen, {"codigo": cod_origen, "nombre": cod_origen, "bandera": ""})
        m_destino = MONEDA_IDX.get(cod_destino, {"codigo": cod_destino, "nombre": cod_destino, "bandera": ""})
        historial.append({
            "cantidad": cantidad,
            "nombre_origen": m_origen.get("nombre", cod_origen),
            "nombre_destino": m_destino.get("nombre", cod_destino),
            "bandera_origen": m_origen.get("bandera", ""),
            "bandera_destino": m_destino.get("bandera", ""),
            "resultado": resultado_str,
            "tasa": f"{float(tasa_val):,.6f}",
        })

    return render_template("index.html", monedas=MONEDAS, historial=historial if historial else None)


@app.route("/convertir", methods=["POST"])
def convertir():
    try:
        data = request.get_json(force=True, silent=False) or {}
        cantidad_raw = data.get("cantidad", "").strip() if isinstance(data.get("cantidad"), str) else data.get("cantidad")
        moneda_origen = str(data.get("moneda_origen", "")).upper()
        moneda_destino = str(data.get("moneda_destino", "")).upper()

        # Validaciones
        if moneda_origen not in MONEDA_IDX or moneda_destino not in MONEDA_IDX:
            return jsonify({"error": "Moneda no válida."}), 400

        try:
            cantidad = float(cantidad_raw)
        except (TypeError, ValueError):
            return jsonify({"error": "Cantidad no válida."}), 400

        if cantidad <= 0:
            return jsonify({"error": "La cantidad debe ser mayor que cero."}), 400

        # Obtener tasa y calcular resultado
        tasa = obtener_tasa(moneda_origen, moneda_destino)
        resultado_val = cantidad * tasa
        resultado_str = _formatear_resultado(moneda_destino, resultado_val)

        # Guardar en historial (resultado como string formateado para mostrar)
        try:
            guardar_conversion(
                cantidad=cantidad,
                moneda_origen=moneda_origen,
                moneda_destino=moneda_destino,
                resultado=resultado_str,
                tasa=float(tasa),
            )
        except Exception as e:
            app.logger.error(f"Error guardando historial: {e}")

        return jsonify({
            "cantidad": cantidad,
            "resultado": resultado_str,
            "tasa": f"{float(tasa):,.6f}",
        })

    except Exception as e:
        app.logger.exception(f"Error en /convertir: {e}")
        return jsonify({"error": "Error interno del servidor."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Debug desactivado por defecto
    app.run(host="0.0.0.0", port=port, debug=False)
