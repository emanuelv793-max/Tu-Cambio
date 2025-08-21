
from flask import Flask, render_template_string, request, jsonify
import requests
import os
import sqlite3
from functools import lru_cache
from datetime import datetime

# --- LÓGICA DE LA BASE DE DATOS ---
def init_db():
    """Inicializa la base de datos de historial."""
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
    """Guarda una conversión en la base de datos."""
    conn = sqlite3.connect('historial.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO historial (cantidad, moneda_origen, moneda_destino, resultado, tasa)
        VALUES (?, ?, ?, ?, ?)
    ''', (cantidad, moneda_origen, moneda_destino, resultado, tasa))
    conn.commit()
    conn.close()

def obtener_historial(limite=10):
    """Obtiene el historial de conversiones."""
    conn = sqlite3.connect('historial.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM historial ORDER BY fecha DESC LIMIT ?', (limite,))
    historial = cursor.fetchall()
    conn.close()
    return historial

# Inicializar la base de datos al arrancar
init_db()

# --- MONEDAS Y CONVERSIÓN ---
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

MONEDA_IDX = {m["codigo"]: m for m in MONEDAS}

import time
# --- Caché rápido de tasas para acelerar respuestas ---
TASAS_CACHE = {}
CACHE_TTL = 20 * 60  # 20 min en segundos

def obtener_tasa(moneda_base, moneda_destino):
    """
    Obtiene la tasa usando caché y una petición rápida (timeout 3s). Si la API falla, intenta usar la última tasa cacheada aún si está "caducada", avisando al usuario si la tasa es antigua.
    """
    now = time.time()
    clave = (moneda_base, moneda_destino)
    # 1. Si en caché válida => usar
    if clave in TASAS_CACHE:
        tasa, timestamp = TASAS_CACHE[clave]
        if now - timestamp < CACHE_TTL:
            return tasa
    # 2. Intentar obtener tasas frescas para moneda_base
    try:
        resp = requests.get(f"https://open.er-api.com/v6/latest/{moneda_base}", timeout=3)
        datos = resp.json()
        if datos["result"] == "success" and moneda_destino in datos["rates"]:
            tasa = float(datos["rates"][moneda_destino])
            TASAS_CACHE[clave] = (tasa, now)
            return tasa
    except Exception as e:
        print(f"Error de API: {e}")
    # 3. Fallback: usar caché vieja (si existe, aunque esté caducada)
    if clave in TASAS_CACHE:
        tasa, timestamp = TASAS_CACHE[clave]
        return tasa
    return None

def _formatear_resultado(moneda_codigo, valor):
    """Formatea el valor del resultado según la moneda."""
    if moneda_codigo in ["PYG", "VES", "JPY"]:
        return f"{valor:,.0f}"
    else:
        return f"{valor:,.2f}"

def _obtener_historial_con_banderas(limite=5):
    """Obtiene el historial y añade las banderas para el frontend."""
    historial = obtener_historial(limite)
    historial_con_banderas = []
    for item in historial:
        # Los elementos del historial: (id, cantidad, origen_cod, destino_cod, resultado, tasa, fecha)
        origen_codigo = item[2]
        destino_codigo = item[3]
        
        # Buscar las banderas
        bandera_origen = MONEDA_IDX.get(origen_codigo, {}).get("bandera", "")
        bandera_destino = MONEDA_IDX.get(destino_codigo, {}).get("bandera", "")
        nombre_origen = MONEDA_IDX.get(origen_codigo, {}).get("nombre", origen_codigo)
        nombre_destino = MONEDA_IDX.get(destino_codigo, {}).get("nombre", destino_codigo)
        
        # Convertir a lista y añadir información adicional
        historial_item = list(item)
        historial_item.extend([bandera_origen, bandera_destino, nombre_origen, nombre_destino])
        historial_con_banderas.append(historial_item)
    return historial_con_banderas

# --- RUTAS ---
app = Flask(__name__)

@app.route("/")
def index():
    historial = _obtener_historial_con_banderas()
    return render_template_string(TEMPLATE, monedas=MONEDAS, historial=historial, MONEDA_IDX=MONEDA_IDX)

@app.route("/convertir", methods=["POST"])
def convertir():
    try:
        data = request.json
        cantidad_raw = data.get("cantidad")
        moneda_origen = data.get("moneda_origen")
        moneda_destino = data.get("moneda_destino")

        # Validar la entrada
        if not all([cantidad_raw, moneda_origen, moneda_destino]):
            return jsonify({"error": "Faltan parámetros."}), 400
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
        if tasa is None:
            # Intentar con monedas invertidas como fallback
            tasa = obtener_tasa(moneda_destino, moneda_origen)
            if tasa is None:
                return jsonify({"error": "No se pudo obtener la tasa de cambio."}), 500
            tasa = 1 / tasa

        resultado_val = cantidad * tasa
        resultado_formateado = _formatear_resultado(moneda_destino, resultado_val)
        nombre_destino = MONEDA_IDX[moneda_destino]["nombre"]
        resultado_str = f"{resultado_formateado} {nombre_destino}"
        
        # Guardar en historial
        try:
            guardar_conversion(
                cantidad=cantidad,
                moneda_origen=moneda_origen,
                moneda_destino=moneda_destino,
                resultado=resultado_str,
                tasa=float(tasa)
            )
        except Exception as e:
            print(f"Error guardando historial: {e}")

        return jsonify({
            "cantidad": cantidad,
            "resultado": resultado_str,
            "tasa": f"{float(tasa):,.6f}",
        })
    
    except Exception as e:
        print(f"Error en /convertir: {e}")
        return jsonify({"error": "Error interno del servidor."}), 500

@app.route("/historial")
def get_historial():
    historial_con_banderas = _obtener_historial_con_banderas()
    return jsonify(historial_con_banderas)


# Template HTML anterior (más simple)
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Conversor de Monedas</title>
    <style>
        body {
            font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
            margin: 0;
            min-height: 100vh;
            /* Fondo imagen Unsplash */
            background: url('https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=1400&q=80') center center/cover no-repeat fixed;
        }
        /* Capa de oscurecimiento y desenfoque para legibilidad */
        body:before {
            content: '';
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(25, 30, 45, 0.48);
            backdrop-filter: blur(4px);
            z-index: 0;
        }
        .container {
            position: relative;
            z-index: 2;
            max-width: 420px;
            margin: 48px auto 0 auto;
            padding: 32px 34px 27px 34px;
            background: rgba(255,255,255,0.88);
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(74,74,120,0.15), 0 1.5px 8px #cdd0fd;
            border: 1.5px solid rgba(80,120,250,0.15);
            backdrop-filter: blur(3px);
        }
        h1 {
            text-align: center;
            color: #2a53a8;
            letter-spacing: 1.6px;
            font-weight: 900;
            margin-bottom: 8px;
            font-size: 2rem;
            text-shadow: 0 2px 6px #cef6f6aa;
        }
        label {
            display: block;
            margin-top: 15px;
            font-size: 1rem;
            color: #2c3046;
            font-weight: 500;
            letter-spacing: 0.1em;
        }
        input, select {
            width: 100%;
            padding: 9px 10px;
            margin-top: 6px;
            font-size: 1em;
            border: 1px solid #e6e6e6;
            border-radius: 7px;
            box-sizing: border-box;
            background: #f4f8fb;
            margin-bottom: 3px;
            transition: border 0.2s;
        }
        input:focus, select:focus {
            outline: none;
            box-shadow: 0 0 0 2px #9ad2fa;
            border: 1.5px solid #9ad2fa;
            background: #fff;
        }
        #convert-btn {
            background: linear-gradient(90deg,#1670e9,#ff7c53);
            color: white;
            font-weight: 700;
            padding: 11px 10px;
            border: none;
            border-radius: 8px;
            margin-top: 18px;
            width: 100%;
            font-size: 1em;
            letter-spacing: 1px;
            cursor: pointer;
            transition: background .17s, box-shadow .14s;
            box-shadow: 0px 1px 5px #e6e7fe;
        }
        #convert-btn:hover {
            background: linear-gradient(90deg,#1670e9,#ffac53);
        }
        .resultado {
            margin-top: 22px;
            padding: 10px;
            border-radius: 7px;
            border: 1.5px solid #e5eaff;
            background-color: #f7f8fc;
            text-align: center;
            min-height: 50px;
        }
        .resultado h2 {
            margin: 0 0 5px 0;
            color: #1670e9;
            font-size: 1.5em;
        }
        .historial {
            margin-top: 24px;
        }
        .historial h3 {
            border-bottom: 1.5px solid #eae9ff;
            padding-bottom: 7px;
            margin-bottom: 11px;
            font-size: 1.15em;
            letter-spacing: 0.03em;
            color: #444;
        }
        .historial ul {
            list-style-type: none;
            padding: 0;
            margin: 0;
        }
        .historial li {
            display: flex;
            align-items: center;
            gap: 7px;
            padding: 6px 0;
            border-bottom: 1px solid #f2eeee;
            font-size: 1em;
        }
        .flag {
            width: 20px; height: 15px;
            border: 1px solid #d7d7d7;
            border-radius: 3px;
            margin-right: 5px;
            background: #f7f7f7;
            object-fit: contain;
        }
        @media (max-width: 600px) {
            .container {
                margin: 0;
                border-radius: 0;
                box-shadow: none;
                padding: 12px 3vw 16px 3vw;
            }
            h1 {
                font-size: 1.2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Conversor Nueva Interfaz</h1>
        <form id="conversion-form">
            <label for="cantidad">Cantidad:</label>
            <input type="number" id="cantidad" value="1" step="0.01" required>

            <label for="moneda_origen">De:</label>
            <select id="moneda_origen">
                {% for moneda in monedas %}
                <option value="{{ moneda['codigo'] }}" {% if moneda['codigo'] == 'USD' %}selected{% endif %}>{{ moneda['nombre'] }} ({{ moneda['codigo'] }})</option>
                {% endfor %}
            </select>

            <label for="moneda_destino">A:</label>
            <select id="moneda_destino">
                {% for moneda in monedas %}
                <option value="{{ moneda['codigo'] }}" {% if moneda['codigo'] == 'EUR' %}selected{% endif %}>{{ moneda['nombre'] }} ({{ moneda['codigo'] }})</option>
                {% endfor %}
            </select>
            
            <button type="button" id="convert-btn">Convertir</button>
        </form>

        <div class="resultado">
            <h2 id="resultado-texto"></h2>
            <p id="tasa-texto"></p>
        </div>

        <!-- Bloque ADSENSE -->
        <div style="margin:22px 0;text-align:center;">
            <!-- Google AdSense (DEMO, reemplaza ca-pub-XXX por tu ID real) -->
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-xxxxxxxxxxxxxxxx"
                crossorigin="anonymous"></script>
            <ins class="adsbygoogle"
                style="display:block; text-align:center; min-height:100px; background: #f6f9fa; border-radius: 8px;"
                data-ad-client="ca-pub-xxxxxxxxxxxxxxxx"
                data-ad-slot="1234567890"
                data-ad-format="auto"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>

        <div class="historial">
            <h3>Historial Reciente</h3>
            <ul id="historial-lista">
                </ul>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const cantidadInput = document.getElementById('cantidad');
            const origenSelect = document.getElementById('moneda_origen');
            const destinoSelect = document.getElementById('moneda_destino');
            const convertBtn = document.getElementById('convert-btn');
            const resultadoTexto = document.getElementById('resultado-texto');
            const tasaTexto = document.getElementById('tasa-texto');
            const historialLista = document.getElementById('historial-lista');

            function actualizarHistorial() {
                fetch('/historial')
                    .then(response => response.json())
                    .then(historial => {
                        historialLista.innerHTML = '';
                        historial.forEach(item => {
                            const li = document.createElement('li');
                            // item: (id, cantidad, origen, destino, resultado, tasa, fecha, bandera_origen, bandera_destino, nombre_origen, nombre_destino)
                            li.innerHTML = `
                                <img class="flag" src="${item[7]}" alt="origen"> <b>${item[1]}</b> ${item[9]}
                                <span style="font-size:1.3em; margin: 0 0.4em;">→</span>
                                <img class="flag" src="${item[8]}" alt="destino"> <b>${item[4]}</b>
                                <span style="font-size:0.85em; color:#778;">${item[6].substring(0, 16).replace('T',' ')}</span>
                            `;
                            historialLista.appendChild(li);
                        });
                        if(historial.length === 0) {
                            const li = document.createElement('li');
                            li.textContent = 'No hay conversiones recientes.';
                            historialLista.appendChild(li);
                        }
                    });
            }

            function convertir() {
                const cantidad = cantidadInput.value;
                const monedaOrigen = origenSelect.value;
                const monedaDestino = destinoSelect.value;

                fetch('/convertir', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        cantidad: cantidad,
                        moneda_origen: monedaOrigen,
                        moneda_destino: monedaDestino
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        resultadoTexto.textContent = `Error: ${data.error}`;
                        tasaTexto.textContent = '';
                    } else {
                        resultadoTexto.textContent = data.resultado;
                        tasaTexto.textContent = `Tasa: 1 ${monedaOrigen} = ${data.tasa} ${monedaDestino}`;
                        actualizarHistorial();
                    }
                })
                .catch(error => {
                    resultadoTexto.textContent = 'Error de conexión';
                    tasaTexto.textContent = '';
                    console.error('Error:', error);
                });
            }

            convertBtn.addEventListener('click', convertir);
            actualizarHistorial();
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)