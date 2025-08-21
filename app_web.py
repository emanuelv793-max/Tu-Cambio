from flask import Flask, render_template_string, request, jsonify
import requests
import os

app = Flask(__name__)

# He agregado más monedas para que tu aplicación sea más completa
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

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Conversor de Monedas</title>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4347223649983931" crossorigin="anonymous"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/choices.js/public/assets/styles/choices.min.css"/>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80') no-repeat center center fixed;
            background-size: cover;
            margin: 0;
            padding: 0;
            transition: background 0.5s;
        }
        .container {
            background: rgba(255,255,255,0.32);
            max-width: 400px;
            margin: 60px auto;
            padding: 30px 30px 20px 30px;
            border-radius: 24px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15), 0 1.5px 8px #bcc2f5;
            border: 1.5px solid rgba(255,255,255,0.38);
            backdrop-filter: blur(16px) saturate(180%);
            -webkit-backdrop-filter: blur(16px) saturate(180%);
            transition: background 0.5s, color 0.5s;
            position: relative;
        }
        .resultado {
            background: rgba(255,255,255,0.16);
            color: #130f40;
            border-radius: 18px;
            padding: 20px 14px;
            margin-top: 22px;
            text-align: center;
            font-size: 1.14em;
            border: 1.5px solid rgba(255,255,255,0.26);
            box-shadow: 0 4px 18px 0 rgba(31, 38, 135, 0.08);
            animation: fadein 0.7s;
            backdrop-filter: blur(16px) saturate(180%);
            -webkit-backdrop-filter: blur(16px) saturate(180%);
            /* Para glass: sin doble border ni color sólido extra al fondo */
        }
        /* Nunca dejar fondo ni min-height ni padding en #resultado-container si está vacío */
        #resultado-container:empty { min-height: 0 !important; padding: 0 !important; background: none !important; border: none !important; }
        
        /* Elimina el espacio del bloque ads vacío */
        #adsense, .adsense {
            display:none !important;
            height:0 !important;
        }
        h2 {
            color: #273c75;
            text-align: center;
            margin-bottom: 30px;
        }
        label {
            font-weight: 500;
            color: #353b48;
        }
        input, select {
            width: 100%;
            padding: 10px;
            margin: 8px 0 18px 0;
            border: 1px solid #dcdde1;
            border-radius: 6px;
            font-size: 1em;
            box-sizing: border-box;
            transition: border 0.3s;
        }
        .flag {
            vertical-align: middle;
            width: 22px;
            height: 16px;
            margin-right: 6px;
            border-radius: 2px;
            box-shadow: 0 1px 2px #aaa2;
        }
        /* Mejoras en el estilo del menú desplegable */
        .choices__item--choice.is-selected {
            background-color: #f5f5f5;
        }
        .choices__item {
            font-size: 1.1em;
        }
        .choices__item--choice {
            display: flex;
            align-items: center;
            padding: 10px;
        }
        .choices__item--choice .flag {
            margin-right: 12px;
        }
        .choices__list--dropdown .choices__item--choice {
            padding: 10px;
        }
        .choices__list--dropdown {
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .choices[data-type*="select-one"] .choices__inner {
            display: flex;
            align-items: center;
        }
        .choices__inner .flag {
            margin-right: 12px;
        }
        .choices__inner .choices__item {
            margin: 0 !important;
        }

        button, .invertir-btn {
            width: 100%;
            background: #273c75;
            color: #fff;
            border: none;
            padding: 12px;
            border-radius: 6px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
            margin-bottom: 10px;
        }
        button:hover, .invertir-btn:hover {
            background: #40739e;
        }
        .invertir-btn {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            margin: 0 auto 18px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f5f6fa;
            color: #273c75;
            border: 2px solid #273c75;
            font-size: 1.5em;
            transition: background 0.2s, color 0.2s;
        }
        .invertir-btn:hover {
            background: #273c75;
            color: #fff;
        }
        .resultado {
            background: #dff9fb;
            color: #130f40;
            border-radius: 6px;
            padding: 15px;
            margin-top: 20px;
            text-align: center;
            font-size: 1.1em;
            border: 1px solid #c7ecee;
            animation: fadein 0.7s;
        }
        #loading {
            display: none;
            text-align: center;
            margin-top: 10px;
            color: #273c75;
        }
        @keyframes fadein {
            from { opacity: 0; transform: translateY(20px);}
            to { opacity: 1; transform: translateY(0);}
        }
        .error {
            color: #c0392b;
            background: #fbeee6;
            border: 1px solid #e17055;
            border-radius: 6px;
            padding: 10px;
            margin-top: 10px;
            text-align: center;
            animation: fadein 0.7s;
        }
        .historial {
            margin-top: 30px;
            background: #f1f2f6;
            border-radius: 8px;
            padding: 10px;
            font-size: 0.98em;
            color: #636e72;
            max-height: 120px;
            overflow-y: auto;
        }
        @media (max-width: 500px) {
            .container { padding: 15px; }
        }
    </style>
</head>
<body>
    <div class="container" id="main-container">
        <h2>Conversor de Monedas</h2>
        <button type="button" class="invertir-btn" id="invertir" title="Invertir monedas">&#8646;</button>
        <form id="formulario" onsubmit="return false;">
            <label>Convertir de:</label>
            <select id="moneda_origen" name="moneda_origen" required>
                {% for m in monedas %}
                <option value="{{m.codigo}}" data-custom-properties='<img src="{{m.bandera}}" class="flag">'
                    {% if m.codigo == 'EUR' %}selected{% endif %}>
                    {{m.nombre}}
                </option>
                {% endfor %}
            </select>
            <label>a:</label>
            <select id="moneda_destino" name="moneda_destino" required>
                {% for m in monedas %}
                <option value="{{m.codigo}}" data-custom-properties='<img src="{{m.bandera}}" class="flag">'
                    {% if m.codigo == 'USD' %}selected{% endif %}>
                    {{m.nombre}}
                </option>
                {% endfor %}
            </select>
            <label>Cantidad:</label>
            <input type="text" name="cantidad" id="cantidad" value="1" required>
        </form>
        <div id="resultado-container" style="min-height:0;"></div>
        <div id="loading">Cargando...</div>
        {% if historial %}
            <div class="historial">
                <strong>Historial de conversiones:</strong>
                <ul style="padding-left:18px;">
                {% for h in historial %}
                    <li>
                        <img src="{{h.bandera_origen}}" class="flag"> {{h.cantidad}} {{h.nombre_origen}}
                        =
                        <img src="{{h.bandera_destino}}" class="flag"> {{h.resultado}}
                        <span style="font-size:0.9em;color:#888;">(Tasa: {{h.tasa}})</span>
                    </li>
                {% endfor %}
                </ul>
            </div>
        {% endif %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/choices.js/public/assets/scripts/choices.min.js"></script>
    <script>
        // Choices.js para selects con banderas
        const choices1 = new Choices('#moneda_origen', {
            searchEnabled: true,
            itemSelectText: '',
            allowHTML: true,
            shouldSort: false,
        });
        const choices2 = new Choices('#moneda_destino', {
            searchEnabled: true,
            itemSelectText: '',
            allowHTML: true,
            shouldSort: false,
        });

        // Botón invertir monedas
        document.getElementById('invertir').onclick = function() {
            let origen = document.getElementById('moneda_origen').value;
            let destino = document.getElementById('moneda_destino').value;
            choices1.setChoiceByValue(destino);
            choices2.setChoiceByValue(origen);
            actualizarConversion();
        };

        // Función para obtener los nombres de las monedas y banderas (JavaScript)
        function getMonedaData(codigo) {
            const monedas = {{ monedas | tojson }};
            return monedas.find(m => m.codigo === codigo);
        }

        // Conversión en tiempo real
        let timeout;
        function actualizarConversion() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const cantidad = document.getElementById('cantidad').value;
                const origen = document.getElementById('moneda_origen').value;
                const destino = document.getElementById('moneda_destino').value;
                const resultadoDiv = document.getElementById('resultado-container');
                const loadingDiv = document.getElementById('loading');

                if (isNaN(cantidad) || parseFloat(cantidad) <= 0 || cantidad.trim() === "") {
                    resultadoDiv.innerHTML = `<div class="error">Por favor, introduce un número válido y mayor que cero.</div>`;
                    document.getElementById('cantidad').style.border = "2px solid #c0392b";
                    return;
                } else {
                    document.getElementById('cantidad').style.border = "";
                }

                loadingDiv.style.display = 'block';

                fetch('/convertir', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        cantidad: cantidad,
                        moneda_origen: origen,
                        moneda_destino: destino
                    }),
                })
                .then(response => response.json())
                .then(data => {
                    loadingDiv.style.display = 'none';
                    if (data.error) {
                        resultadoDiv.innerHTML = `<div class="error">${data.error}</div>`;
                    } else {
                        const m_origen = getMonedaData(origen);
                        const m_destino = getMonedaData(destino);
                        resultadoDiv.innerHTML = `
                            <div class="resultado">
                                <strong>Resultado:</strong><br>
                                <img src="${m_origen.bandera}" class="flag"> ${data.cantidad} ${m_origen.nombre}
                                =
                                <img src="${m_destino.bandera}" class="flag"> ${data.resultado}
                                <br>
                                <span style="font-size:0.95em;color:#888;">Tasa: ${data.tasa}</span>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    loadingDiv.style.display = 'none';
                    resultadoDiv.innerHTML = `<div class="error">Ocurrió un error. Intenta de nuevo más tarde.</div>`;
                    console.error('Error:', error);
                });
            }, 500); // 500 ms de espera
        }

        document.getElementById('cantidad').addEventListener('input', actualizarConversion);
        document.getElementById('moneda_origen').addEventListener('change', actualizarConversion);
        document.getElementById('moneda_destino').addEventListener('change', actualizarConversion);

        // Inicia la conversión al cargar la página
        actualizarConversion();

    </script>
</body>
</html>
"""

# Historial en memoria (solo para la sesión actual del servidor)
historial_global = []

def obtener_tasa(base, destino, defecto):
    try:
        respuesta = requests.get(f"https://open.er-api.com/v6/latest/{base}", timeout=5)
        respuesta.raise_for_status() # Lanza un error para HTTP 4xx/5xx
        datos = respuesta.json()
        return datos["rates"][destino]
    except (requests.exceptions.RequestException, KeyError):
        return defecto

def buscar_moneda(codigo):
    return next((m for m in MONEDAS if m["codigo"] == codigo), None)

@app.route("/", methods=["GET"])
def index():
    return render_template_string(
        TEMPLATE,
        monedas=MONEDAS,
        historial=historial_global if historial_global else None
    )

@app.route("/convertir", methods=["POST"])
def convertir():
    try:
        data = request.json
        cantidad = data.get("cantidad")
        moneda_origen = data.get("moneda_origen")
        moneda_destino = data.get("moneda_destino")

        cantidad_float = float(cantidad)
        if cantidad_float <= 0:
            return jsonify({"error": "Por favor, introduce un número válido y mayor que cero."})

        m_origen = buscar_moneda(moneda_origen)
        m_destino = buscar_moneda(moneda_destino)

        if not m_origen or not m_destino:
            return jsonify({"error": "Moneda no válida."})

        nombre_origen = m_origen["nombre"]
        nombre_destino = m_destino["nombre"]
        
        # Tasas de defecto para fallos de la API
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
        defecto = tasas_defecto.get((moneda_origen, moneda_destino), 1.0)
        
        tasa_valor = obtener_tasa(moneda_origen, moneda_destino, defecto)
        convertido = cantidad_float * tasa_valor
        
        if moneda_destino in ["PYG", "VES"]:
            resultado_formato = f"{convertido:,.0f} {nombre_destino}"
        else:
            resultado_formato = f"{convertido:,.2f} {nombre_destino}"
        
        tasa_formato = f"{tasa_valor:,.6f}"
        
        # Guardar en historial (máximo 5)
        historial_global.insert(0, {
            "cantidad": cantidad,
            "nombre_origen": nombre_origen,
            "nombre_destino": nombre_destino,
            "bandera_origen": m_origen["bandera"],
            "bandera_destino": m_destino["bandera"],
            "resultado": resultado_formato,
            "tasa": tasa_formato
        })
        if len(historial_global) > 5:
            historial_global.pop()
        
        return jsonify({
            "cantidad": cantidad,
            "resultado": resultado_formato,
            "tasa": tasa_formato
        })

    except ValueError:
        return jsonify({"error": "Por favor, introduce un número válido y mayor que cero."})
    except Exception:
        return jsonify({"error": "Ocurrió un error. Intenta de nuevo más tarde."})

@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)