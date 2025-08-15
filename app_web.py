from flask import Flask, render_template_string, request
import requests
import os

app = Flask(__name__)

MONEDAS = [
    {"codigo": "EUR", "nombre": "Euro", "bandera": "https://flagcdn.com/eu.svg"},
    {"codigo": "USD", "nombre": "Dólar estadounidense", "bandera": "https://flagcdn.com/us.svg"},
    {"codigo": "VES", "nombre": "Bolívar venezolano", "bandera": "https://flagcdn.com/ve.svg"},
    {"codigo": "PYG", "nombre": "Guaraní paraguayo", "bandera": "https://flagcdn.com/py.svg"},
]

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Conversor de Monedas</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Choices.js CDN para selects con banderas -->
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
            background: rgba(255,255,255,0.92);
            max-width: 400px;
            margin: 60px auto;
            padding: 30px 30px 20px 30px;
            border-radius: 15px;
            box-shadow: 0 4px 24px rgba(44, 62, 80, 0.12);
            transition: background 0.5s, color 0.5s;
            position: relative;
        }
        .modo-oscuro-btn {
            position: absolute;
            top: 18px;
            right: 18px;
            background: none;
            border: none;
            font-size: 1.7em;
            cursor: pointer;
            outline: none;
            z-index: 10;
            transition: color 0.2s;
        }
        .modo-oscuro-btn:hover {
            color: #40739e;
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
        .option-flag {
            display: inline-flex;
            align-items: center;
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
        .dark-mode body {
            background: #23272f !important;
        }
        .dark-mode .container {
            background: rgba(30,34,40,0.97) !important;
            color: #f5f6fa !important;
        }
        .dark-mode h2, .dark-mode label {
            color: #f5f6fa !important;
        }
        .dark-mode input, .dark-mode select {
            background: #23272f !important;
            color: #f5f6fa !important;
            border: 1px solid #353b48 !important;
        }
        .dark-mode .resultado {
            background: #353b48 !important;
            color: #f5f6fa !important;
            border: 1px solid #23272f !important;
        }
        .dark-mode .error {
            background: #2d3436 !important;
            color: #fab1a0 !important;
            border: 1px solid #d63031 !important;
        }
        .dark-mode button, .dark-mode .invertir-btn {
            background: #353b48 !important;
            color: #f5f6fa !important;
            border: 2px solid #636e72 !important;
        }
        .dark-mode button:hover, .dark-mode .invertir-btn:hover {
            background: #636e72 !important;
            color: #fff !important;
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
        .dark-mode .historial {
            background: #23272f !important;
            color: #b2bec3 !important;
        }
        @media (max-width: 500px) {
            .container { padding: 15px; }
            .modo-oscuro-btn { top: 8px; right: 8px; font-size: 1.3em;}
        }
    </style>
</head>
<body>
    <div class="container" id="main-container">
        <button type="button" class="modo-oscuro-btn" id="modo-oscuro" title="Modo oscuro/claro">🌙</button>
        <h2>Conversor de Monedas</h2>
        <button type="button" class="invertir-btn" id="invertir" title="Invertir monedas">&#8646;</button>
        <form method="post" id="formulario">
            <label>Convertir de:</label>
            <select id="moneda_origen" name="moneda_origen" required>
                {% for m in monedas %}
                <option value="{{m.codigo}}" data-custom-properties='<img src="{{m.bandera}}" class="flag">'
                    {% if m.codigo == moneda_origen %}selected{% endif %}>
                    {{m.nombre}}
                </option>
                {% endfor %}
            </select>
            <label>a:</label>
            <select id="moneda_destino" name="moneda_destino" required>
                {% for m in monedas %}
                <option value="{{m.codigo}}" data-custom-properties='<img src="{{m.bandera}}" class="flag">'
                    {% if m.codigo == moneda_destino %}selected{% endif %}>
                    {{m.nombre}}
                </option>
                {% endfor %}
            </select>
            <label>Cantidad:</label>
            <input type="text" name="cantidad" id="cantidad" value="{{cantidad or ''}}" required>
            <button type="submit">Convertir</button>
        </form>
        {% if resultado %}
            {% if error %}
                <div class="error">{{ resultado }}</div>
            {% else %}
                <div class="resultado">
                    <strong>Resultado:</strong><br>
                    <img src="{{bandera_origen}}" class="flag"> {{cantidad}} {{nombre_origen}}
                    =
                    <img src="{{bandera_destino}}" class="flag"> {{resultado}}
                    <br>
                    <span style="font-size:0.95em;color:#888;">Tasa: {{tasa}}</span>
                </div>
            {% endif %}
        {% endif %}
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
            searchEnabled: false,
            itemSelectText: '',
            allowHTML: true,
            shouldSort: false,
        });
        const choices2 = new Choices('#moneda_destino', {
            searchEnabled: false,
            itemSelectText: '',
            allowHTML: true,
            shouldSort: false,
        });

        // Botón invertir monedas
        document.getElementById('invertir').onclick = function() {
            let origen = document.getElementById('moneda_origen');
            let destino = document.getElementById('moneda_destino');
            let temp = origen.value;
            origen.value = destino.value;
            destino.value = temp;
            choices1.setChoiceByValue(origen.value);
            choices2.setChoiceByValue(destino.value);
        };

        // Modo oscuro/claro
        document.getElementById('modo-oscuro').onclick = function() {
            document.body.classList.toggle('dark-mode');
            document.getElementById('main-container').classList.toggle('dark-mode');
            // Cambia el icono según el modo
            this.textContent = document.body.classList.contains('dark-mode') ? '☀️' : '🌙';
        };

        // Validación visual de errores
        document.getElementById('formulario').onsubmit = function(e) {
            let cantidad = document.getElementById('cantidad').value;
            if (isNaN(cantidad) || cantidad.trim() === "" || Number(cantidad) <= 0) {
                alert("Por favor, introduce un número válido y mayor que cero.");
                document.getElementById('cantidad').style.border = "2px solid #c0392b";
                e.preventDefault();
                return false;
            } else {
                document.getElementById('cantidad').style.border = "";
            }
        };
    </script>
</body>
</html>
"""

def obtener_tasa(base, destino, defecto):
    try:
        respuesta = requests.get(f"https://open.er-api.com/v6/latest/{base}")
        datos = respuesta.json()
        return datos["rates"][destino]
    except Exception:
        return defecto

def buscar_moneda(codigo):
    for m in MONEDAS:
        if m["codigo"] == codigo:
            return m
    return None

# Historial en memoria (solo para la sesión actual del servidor)
historial_global = []

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = ""
    tasa = ""
    cantidad = ""
    moneda_origen = "EUR"
    moneda_destino = "USD"
    nombre_origen = ""
    nombre_destino = ""
    bandera_origen = ""
    bandera_destino = ""
    error = False
    if request.method == "POST":
        moneda_origen = request.form.get("moneda_origen", "EUR")
        moneda_destino = request.form.get("moneda_destino", "USD")
        cantidad = request.form.get("cantidad", "")
        m_origen = buscar_moneda(moneda_origen)
        m_destino = buscar_moneda(moneda_destino)
        nombre_origen = m_origen["nombre"]
        nombre_destino = m_destino["nombre"]
        bandera_origen = m_origen["bandera"]
        bandera_destino = m_destino["bandera"]
        try:
            cantidad_float = float(cantidad)
            if cantidad_float <= 0:
                raise ValueError
            if moneda_origen == moneda_destino:
                resultado = f"{cantidad_float:,.2f} {nombre_destino}"
                tasa = "1.00"
            else:
                defecto = {
                    ("EUR", "USD"): 1.09,
                    ("USD", "EUR"): 0.92,
                    ("EUR", "VES"): 39.00,
                    ("USD", "VES"): 35.00,
                    ("EUR", "PYG"): 8000.00,
                    ("USD", "PYG"): 7300.00,
                    ("PYG", "VES"): 0.0045,
                    ("VES", "PYG"): 220.00,
                    ("PYG", "USD"): 0.00014,
                    ("VES", "USD"): 0.028,
                    ("PYG", "EUR"): 0.00012,
                    ("VES", "EUR"): 0.025,
                }.get((moneda_origen, moneda_destino), 1.0)
                tasa_valor = obtener_tasa(moneda_origen, moneda_destino, defecto)
                convertido = cantidad_float * tasa_valor
                if moneda_destino in ["PYG", "VES"]:
                    resultado = f"{convertido:,.0f} {nombre_destino}"
                else:
                    resultado = f"{convertido:,.2f} {nombre_destino}"
                tasa = f"{tasa_valor:,.6f}"
            # Guardar en historial (máximo 5)
            historial_global.insert(0, {
                "cantidad": cantidad,
                "nombre_origen": nombre_origen,
                "nombre_destino": nombre_destino,
                "bandera_origen": bandera_origen,
                "bandera_destino": bandera_destino,
                "resultado": resultado,
                "tasa": tasa
            })
            if len(historial_global) > 5:
                historial_global.pop()
        except ValueError:
            resultado = "Por favor, introduce un número válido y mayor que cero."
            error = True
    else:
        m_origen = buscar_moneda(moneda_origen)
        m_destino = buscar_moneda(moneda_destino)
        nombre_origen = m_origen["nombre"]
        nombre_destino = m_destino["nombre"]
        bandera_origen = m_origen["bandera"]
        bandera_destino = m_destino["bandera"]
    return render_template_string(
        TEMPLATE,
        monedas=MONEDAS,
        resultado=resultado,
        tasa=tasa,
        cantidad=cantidad,
        moneda_origen=moneda_origen,
        moneda_destino=moneda_destino,
        nombre_origen=nombre_origen,
        nombre_destino=nombre_destino,
        bandera_origen=bandera_origen,
        bandera_destino=bandera_destino,
        historial=historial_global if historial_global else None,
        error=error
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
