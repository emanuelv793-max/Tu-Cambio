from flask import Flask, render_template_string, request
import requests

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
    <style>
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80') no-repeat center center fixed;
            background-size: cover;
            margin: 0; 
            padding: 0;
        }
        .container {
            background: rgba(255,255,255,0.92);
            max-width: 400px;
            margin: 60px auto;
            padding: 30px 30px 20px 30px;
            border-radius: 15px;
            box-shadow: 0 4px 24px rgba(44, 62, 80, 0.12);
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
        button {
            width: 100%;
            background: #273c75;
            color: #fff;
            border: none;
            padding: 12px;
            border-radius: 6px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover {
            background: #40739e;
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
        }
        @media (max-width: 500px) {
            .container { padding: 15px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Conversor de Monedas</h2>
        <form method="post">
            <label>Convertir de:</label>
            <select name="moneda_origen" required>
                {% for m in monedas %}
                <option value="{{m.codigo}}" {% if m.codigo == moneda_origen %}selected{% endif %}>
                    {{m.nombre}}
                </option>
                {% endfor %}
            </select>
            <label>a:</label>
            <select name="moneda_destino" required>
                {% for m in monedas %}
                <option value="{{m.codigo}}" {% if m.codigo == moneda_destino %}selected{% endif %}>
                    {{m.nombre}}
                </option>
                {% endfor %}
            </select>
            <label>Cantidad:</label>
            <input type="text" name="cantidad" value="{{cantidad or ''}}" required>
            <button type="submit">Convertir</button>
        </form>
        {% if resultado %}
            <div class="resultado">
                <strong>Resultado:</strong><br>
                <img src="{{bandera_origen}}" class="flag"> {{cantidad}} {{nombre_origen}}
                =
                <img src="{{bandera_destino}}" class="flag"> {{resultado}}
                <br>
                <span style="font-size:0.95em;color:#888;">Tasa: {{tasa}}</span>
            </div>
        {% endif %}
    </div>
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
        except ValueError:
            resultado = "Por favor, introduce un número válido."
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
        bandera_destino=bandera_destino
    )

if __name__ == "__main__":
    app.run(debug=True)