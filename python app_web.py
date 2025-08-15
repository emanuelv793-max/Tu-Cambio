from flask import Flask, render_template, request
import requests

app = Flask(__name__)

def obtener_tasa(moneda_base, moneda_destino, valor_defecto):
    try:
        respuesta = requests.get(f"https://open.er-api.com/v6/latest/{moneda_base}")
        datos = respuesta.json()
        return datos["rates"][moneda_destino]
    except Exception:
        print(f"No se pudo obtener la tasa de cambio actual. Usando valor por defecto {valor_defecto}.")
        return valor_defecto

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    tasa = None
    cantidad = None
    origen = None
    destino = None
    if request.method == "POST":
        cantidad = float(request.form["cantidad"])
        origen = request.form["origen"]
        destino = request.form["destino"]
        tasas_defecto = {
            ("EUR", "USD"): 1.09,
            ("EUR", "VES"): 39.00,
            ("USD", "EUR"): 0.92,
            ("USD", "VES"): 35.00,
        }
        valor_defecto = tasas_defecto.get((origen, destino), 1.0)
        tasa = obtener_tasa(origen, destino, valor_defecto)
        resultado = cantidad * tasa
    return render_template("index.html", resultado=resultado, tasa=tasa, cantidad=cantidad, origen=origen, destino=destino)

if __name__ == "__main__":
    app.run(debug=True)

