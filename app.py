from __future__ import annotations

import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

from flask import (
    Flask,
    abort,
    current_app,
    jsonify,
    make_response,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from currencies import (
    CURRENCIES,
    CURRENCY_INDEX,
    DEFAULT_BASE_CURRENCY,
    DEFAULT_QUOTE_CURRENCY,
    FEATURED_PAIRS,
    INDEXABLE_PAIRS,
)
from database import fetch_recent_history, init_db, record_conversion, register_alert_subscription
from rate_service import RateQuote, RateService

WHOLE_NUMBER_CURRENCIES = {"JPY", "KRW", "PYG", "VES"}
DEFAULT_HISTORY_LIMIT = 6
DEFAULT_PUBLIC_BASE_URL = "https://tu-cambio.vercel.app"


def resolve_database_path() -> Path:
    if "DATABASE_PATH" in os.environ:
        return Path(os.environ["DATABASE_PATH"])
    if (
        os.environ.get("VERCEL")
        or os.environ.get("VERCEL_ENV")
        or os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        or os.environ.get("LAMBDA_TASK_ROOT")
    ):
        return Path("/tmp/tu-cambio.db")
    return Path(__file__).resolve().parent / "historial.db"


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        APP_NAME="Tu Cambio",
        PUBLIC_BASE_URL=os.environ.get("PUBLIC_BASE_URL", DEFAULT_PUBLIC_BASE_URL).rstrip("/"),
        DATABASE_PATH=resolve_database_path(),
        RATE_CACHE_TTL_SECONDS=int(os.environ.get("RATE_CACHE_TTL_SECONDS", "900")),
        RATE_REQUEST_TIMEOUT_SECONDS=float(os.environ.get("RATE_REQUEST_TIMEOUT_SECONDS", "5")),
        HISTORY_LIMIT=DEFAULT_HISTORY_LIMIT,
    )

    if test_config:
        app.config.update(test_config)

    init_db(app.config["DATABASE_PATH"])
    app.extensions["rate_service"] = app.config.get(
        "RATE_SERVICE",
        RateService(
            ttl_seconds=app.config["RATE_CACHE_TTL_SECONDS"],
            timeout_seconds=app.config["RATE_REQUEST_TIMEOUT_SECONDS"],
        ),
    )

    @app.after_request
    def apply_response_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), camera=(), microphone=()")
        if request.method == "GET" and request.endpoint in {"home", "pair_page", "sitemap", "robots"}:
            response.headers.setdefault("Cache-Control", "public, s-maxage=3600, stale-while-revalidate=86400")
        elif request.method != "GET" or request.endpoint in {"convert", "history", "subscribe_alerts"}:
            response.headers.setdefault("Cache-Control", "no-store")
        if request.path.startswith("/static/"):
            response.headers.setdefault("Cache-Control", "public, max-age=86400")
        return response

    @app.route("/")
    def home():
        return render_pair_page(DEFAULT_BASE_CURRENCY, DEFAULT_QUOTE_CURRENCY, canonical_home=True)

    @app.route("/cambio/<pair_slug>")
    def pair_page(pair_slug: str):
        base_currency, quote_currency = parse_pair_slug(pair_slug)
        if not base_currency or not quote_currency:
            abort(404)
        return render_pair_page(base_currency, quote_currency)

    @app.route("/convertir", methods=["POST"])
    def convert():
        payload = request.get_json(silent=True) or {}
        amount_value = payload.get("cantidad")
        base_currency = normalize_currency_code(payload.get("moneda_origen"))
        quote_currency = normalize_currency_code(payload.get("moneda_destino"))

        if base_currency not in CURRENCY_INDEX or quote_currency not in CURRENCY_INDEX:
            return jsonify({"error": "Selecciona dos divisas validas."}), 400

        try:
            amount = parse_amount(amount_value)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        if base_currency == quote_currency:
            conversion_payload = build_same_currency_payload(amount, base_currency)
        else:
            rate_quote = resolve_rate_quote(base_currency, quote_currency)
            if rate_quote is None:
                return jsonify({"error": "No hemos podido obtener el tipo de cambio ahora mismo."}), 503
            conversion_payload = build_conversion_payload(amount, base_currency, quote_currency, rate_quote)

        history_item = persist_conversion(conversion_payload)
        conversion_payload["history_item"] = history_item
        conversion_payload["pair_slug"] = build_pair_slug(base_currency, quote_currency)
        conversion_payload["share_url"] = url_for(
            "pair_page",
            pair_slug=build_pair_slug(base_currency, quote_currency),
        )
        return jsonify(conversion_payload)

    @app.route("/historial")
    def history():
        limit = request.args.get("limite", default=app.config["HISTORY_LIMIT"], type=int)
        history_items = get_history_payload(limit=max(1, min(limit, 20)))
        return jsonify(history_items)

    @app.route("/suscribirse-alertas", methods=["POST"])
    def subscribe_alerts():
        payload = request.get_json(silent=True) or {}
        email = str(payload.get("email", "")).strip().lower()
        base_currency = normalize_currency_code(payload.get("moneda_origen"))
        quote_currency = normalize_currency_code(payload.get("moneda_destino"))

        if not is_valid_email(email):
            return jsonify({"error": "Introduce un correo valido para la lista beta."}), 400

        if base_currency not in CURRENCY_INDEX or quote_currency not in CURRENCY_INDEX:
            return jsonify({"error": "Selecciona un par de divisas valido para apuntarte."}), 400

        created = register_alert_subscription(
            app.config["DATABASE_PATH"],
            email=email,
            base_currency=base_currency,
            quote_currency=quote_currency,
        )

        if created:
            message = "Perfecto. Te hemos apuntado a la lista beta de alertas para este par."
        else:
            message = "Ya estabas apuntado a la lista beta para este par."

        return jsonify({"ok": True, "message": message})

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/robots.txt")
    def robots():
        sitemap_url = public_url("/sitemap.xml")
        response = make_response(
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /convertir\n"
            "Disallow: /historial\n"
            "Disallow: /suscribirse-alertas\n"
            f"Sitemap: {sitemap_url}\n"
        )
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        return response

    @app.route("/sitemap.xml")
    def sitemap():
        namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
        urlset = Element("urlset", xmlns=namespace)

        urls = [(public_url("/"), "1.0")]
        urls.extend(
            (public_url(url_for("pair_page", pair_slug=build_pair_slug(base, quote))), "0.8")
            for base, quote in INDEXABLE_PAIRS
        )

        for location, priority in urls:
            url_node = SubElement(urlset, "url")
            SubElement(url_node, "loc").text = location
            SubElement(url_node, "changefreq").text = "daily"
            SubElement(url_node, "priority").text = priority

        response = make_response(tostring(urlset, encoding="unicode"))
        response.headers["Content-Type"] = "application/xml; charset=utf-8"
        return response

    @app.route("/ads.txt")
    def ads():
        ads_file = Path(app.root_path) / "ads.txt"
        if not ads_file.exists():
            abort(404)
        return send_from_directory(app.root_path, "ads.txt")

    @app.route("/favicon.ico")
    def favicon():
        return current_app.send_static_file("icon.svg")

    @app.route("/google91d8c072ad165708.html")
    def google_verification():
        return "google-site-verification: google91d8c072ad165708.html", 200, {"Content-Type": "text/html"}

    return app


def public_url(path: str) -> str:
    """Build stable canonical URLs even when Vercel serves a preview hostname."""
    return f"{current_app.config['PUBLIC_BASE_URL']}/{path.lstrip('/')}"


def build_seo_content(
    base_details: dict[str, str],
    quote_details: dict[str, str],
    *,
    canonical_home: bool,
) -> dict[str, Any]:
    base_name = base_details["name"]
    quote_name = quote_details["name"]
    base_code = base_details["code"]
    quote_code = quote_details["code"]

    if canonical_home:
        title = "Conversor de divisas y tipos de cambio | Tu Cambio"
        description = (
            "Convierte más de 30 monedas con tipos de cambio de referencia actualizados. "
            "Calculadora gratis, rápida y clara para viajes, compras y remesas."
        )
        heading = "Conversor de divisas rápido y gratuito"
        intro = (
            "Calcula cuánto vale una cantidad en otra moneda y consulta la tasa aplicada. "
            "Elige entre monedas de América, Europa y Asia sin crear una cuenta."
        )
    else:
        title = f"{base_code} a {quote_code}: convertir {base_name} a {quote_name} | Tu Cambio"
        description = (
            f"Convierte {base_code} a {quote_code} con la tasa de referencia más reciente. "
            f"Calculadora gratuita de {base_name} a {quote_name}, fácil y rápida."
        )
        heading = f"Convertir {base_name} a {quote_name} ({base_code}/{quote_code})"
        intro = (
            f"Usa esta calculadora para estimar el valor de {base_name} en {quote_name}. "
            f"Escribe cualquier cantidad en {base_code}; el resultado en {quote_code} y la tasa utilizada aparecen automáticamente."
        )

    faq_items = [
        {
            "question": f"¿Cómo convertir {base_code} a {quote_code}?",
            "answer": (
                f"Introduce la cantidad en {base_code}, comprueba que {quote_code} sea la moneda de destino "
                "y la calculadora mostrará el resultado y el tipo de cambio aplicado."
            ),
        },
        {
            "question": "¿La tasa incluye comisiones bancarias?",
            "answer": (
                "No. Mostramos una tasa de referencia del mercado. Tu banco, tarjeta, casa de cambio o plataforma "
                "de envío puede aplicar un margen, una comisión o una tasa diferente."
            ),
        },
        {
            "question": "¿Con qué frecuencia se actualiza el tipo de cambio?",
            "answer": (
                "La calculadora consulta una fuente externa de referencia y reutiliza temporalmente la última respuesta "
                "para mantener el servicio rápido. La fecha de actualización se muestra junto al resultado."
            ),
        },
        {
            "question": f"¿Dónde se usan {base_code} y {quote_code}?",
            "answer": (
                f"El {base_name} se utiliza en {base_details['region']}; el {quote_name}, en {quote_details['region']}. "
                "Comprueba siempre las condiciones del proveedor con el que realizarás la operación."
            ),
        },
    ]

    return {
        "title": title,
        "description": description,
        "heading": heading,
        "intro": intro,
        "baseCode": base_code,
        "quoteCode": quote_code,
        "baseName": base_name,
        "quoteName": quote_name,
        "baseRegion": base_details["region"],
        "quoteRegion": quote_details["region"],
        "faqItems": faq_items,
    }


def build_structured_data(
    *,
    canonical_url: str,
    pair_label: str,
    base_details: dict[str, str],
    quote_details: dict[str, str],
    seo_content: dict[str, Any],
    canonical_home: bool,
) -> dict[str, Any]:
    graph: list[dict[str, Any]] = [
        {
            "@type": "WebSite",
            "@id": f"{current_app.config['PUBLIC_BASE_URL']}/#website",
            "url": f"{current_app.config['PUBLIC_BASE_URL']}/",
            "name": current_app.config["APP_NAME"],
            "inLanguage": "es",
            "description": "Conversor de divisas gratuito con tipos de cambio de referencia.",
        },
        {
            "@type": "WebApplication",
            "@id": f"{canonical_url}#app",
            "name": "Tu Cambio",
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Cualquier dispositivo con navegador web",
            "isAccessibleForFree": True,
            "inLanguage": "es",
            "description": seo_content["description"],
            "url": canonical_url,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
        },
        {
            "@type": "FAQPage",
            "@id": f"{canonical_url}#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                }
                for item in seo_content["faqItems"]
            ],
        },
    ]

    if not canonical_home:
        graph.append(
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Conversor de divisas",
                        "item": public_url("/"),
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": f"{base_details['code']} a {quote_details['code']}",
                        "item": canonical_url,
                    },
                ],
            }
        )

    return {"@context": "https://schema.org", "@graph": graph}


def render_pair_page(base_currency: str, quote_currency: str, canonical_home: bool = False):
    base_details = get_currency(base_currency)
    quote_details = get_currency(quote_currency)
    pair_label = f"{base_details['name']} a {quote_details['name']}"
    pair_slug = build_pair_slug(base_currency, quote_currency)
    canonical_path = "/" if canonical_home else url_for("pair_page", pair_slug=pair_slug)
    canonical_url = public_url(canonical_path)
    seo_content = build_seo_content(base_details, quote_details, canonical_home=canonical_home)
    quick_pairs = [
        {
            "label": f"{get_currency(base)['code']} / {get_currency(quote)['code']}",
            "description": f"{get_currency(base)['name']} a {get_currency(quote)['name']}",
            "href": url_for("pair_page", pair_slug=build_pair_slug(base, quote)),
            "baseCurrency": base,
            "quoteCurrency": quote,
            "active": base == base_currency and quote == quote_currency,
        }
        for base, quote in FEATURED_PAIRS
    ]

    seo_schema = build_structured_data(
        canonical_url=canonical_url,
        pair_label=pair_label,
        base_details=base_details,
        quote_details=quote_details,
        seo_content=seo_content,
        canonical_home=canonical_home,
    )

    bootstrap_data = {
        "appName": current_app.config["APP_NAME"],
        "currencies": CURRENCIES,
        "selectedPair": {
            "baseCurrency": base_currency,
            "quoteCurrency": quote_currency,
            "pairLabel": pair_label,
            "pairSlug": pair_slug,
            "baseName": base_details["name"],
            "quoteName": quote_details["name"],
        },
        "liveSnapshot": {
            "amountDisplay": "1",
            "convertedAmountDisplay": "—",
            "rateDisplay": "—",
            "provider": "Consultando fuente",
            "lastUpdated": "Calculando…",
            "nextUpdate": "",
        },
        "quickPairs": quick_pairs,
        "historyItems": [],
        "seoContent": seo_content,
        "metrics": {
            "currencies": len(CURRENCIES),
            "featuredPairs": len(FEATURED_PAIRS),
            "history": 0,
        },
        "historyLimit": current_app.config["HISTORY_LIMIT"],
        "endpoints": {
            "convert": url_for("convert"),
            "subscribe": url_for("subscribe_alerts"),
            "history": url_for("history"),
            "home": url_for("home"),
        },
    }

    return render_template(
        "index.html",
        app_name=current_app.config["APP_NAME"],
        page_title=seo_content["title"],
        page_description=seo_content["description"],
        canonical_url=canonical_url,
        seo_schema=seo_schema,
        bootstrap_data=bootstrap_data,
        seo_content=seo_content,
        base_currency=base_currency,
        quote_currency=quote_currency,
        quick_pairs=quick_pairs,
        robots_content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1",
        frontend_css_url=url_for("static", filename="app-dist/assets/app.css"),
        frontend_js_url=url_for("static", filename="app-dist/assets/app.js"),
    )


def build_same_currency_payload(amount: float, currency_code: str) -> dict[str, Any]:
    currency = get_currency(currency_code)
    amount_display = format_amount(amount, currency_code)
    return {
        "amount": amount,
        "amount_display": amount_display,
        "base_currency": currency_code,
        "base_name": currency["name"],
        "quote_currency": currency_code,
        "quote_name": currency["name"],
        "converted_amount": amount,
        "converted_amount_display": amount_display,
        "result_display": f"{amount_display} {currency_code}",
        "rate": 1.0,
        "rate_display": "1.000000",
        "provider": "Local",
        "source_url": "",
        "last_updated": "Instantaneo",
        "next_update": "",
        "stale": False,
    }


def build_conversion_payload(
    amount: float,
    base_currency: str,
    quote_currency: str,
    rate_quote: RateQuote,
) -> dict[str, Any]:
    base_details = get_currency(base_currency)
    quote_details = get_currency(quote_currency)
    converted_amount = amount * rate_quote.rate

    return {
        "amount": amount,
        "amount_display": format_amount(amount, base_currency),
        "base_currency": base_currency,
        "base_name": base_details["name"],
        "quote_currency": quote_currency,
        "quote_name": quote_details["name"],
        "converted_amount": converted_amount,
        "converted_amount_display": format_amount(converted_amount, quote_currency),
        "result_display": f"{format_amount(converted_amount, quote_currency)} {quote_currency}",
        "rate": rate_quote.rate,
        "rate_display": format_rate(rate_quote.rate),
        "provider": rate_quote.provider,
        "source_url": rate_quote.source_url,
        "last_updated": rate_quote.last_updated or "Sin dato",
        "next_update": rate_quote.next_update or "",
        "stale": rate_quote.stale,
    }


def persist_conversion(conversion_payload: dict[str, Any]) -> dict[str, Any]:
    record_conversion(
        current_app.config["DATABASE_PATH"],
        amount=conversion_payload["amount"],
        base_currency=conversion_payload["base_currency"],
        quote_currency=conversion_payload["quote_currency"],
        converted_amount=conversion_payload["converted_amount"],
        converted_amount_display=conversion_payload["converted_amount_display"],
        rate=conversion_payload["rate"],
        rate_display=conversion_payload["rate_display"],
        provider=conversion_payload["provider"],
        is_stale=conversion_payload["stale"],
    )

    return {
        "amount_display": conversion_payload["amount_display"],
        "base_currency": conversion_payload["base_currency"],
        "base_name": conversion_payload["base_name"],
        "base_flag": get_currency(conversion_payload["base_currency"])["flag_url"],
        "quote_currency": conversion_payload["quote_currency"],
        "quote_name": conversion_payload["quote_name"],
        "quote_flag": get_currency(conversion_payload["quote_currency"])["flag_url"],
        "converted_amount_display": conversion_payload["converted_amount_display"],
        "rate_display": conversion_payload["rate_display"],
        "provider": conversion_payload["provider"],
        "stale": conversion_payload["stale"],
        "created_at": "Ahora mismo",
    }


def get_history_payload(limit: int | None = None) -> list[dict[str, Any]]:
    history_rows = fetch_recent_history(
        current_app.config["DATABASE_PATH"],
        limit=limit or current_app.config["HISTORY_LIMIT"],
    )
    items: list[dict[str, Any]] = []
    for row in history_rows:
        base_currency = row["base_currency"]
        quote_currency = row["quote_currency"]
        base_details = get_currency(base_currency)
        quote_details = get_currency(quote_currency)
        created_at = format_history_timestamp(row["created_at"])
        items.append(
            {
                "amount_display": format_amount(row["amount"], base_currency),
                "base_currency": base_currency,
                "base_name": base_details["name"],
                "base_flag": base_details["flag_url"],
                "quote_currency": quote_currency,
                "quote_name": quote_details["name"],
                "quote_flag": quote_details["flag_url"],
                "converted_amount_display": row["converted_amount_display"],
                "rate_display": row["rate_display"],
                "provider": row["provider"],
                "stale": bool(row["is_stale"]),
                "created_at": created_at,
            }
        )
    return items


def resolve_rate_quote(base_currency: str, quote_currency: str) -> RateQuote | None:
    rate_service: RateService = current_app.extensions["rate_service"]
    direct_quote = rate_service.get_rate(base_currency, quote_currency)
    if direct_quote is not None:
        return direct_quote

    inverse_quote = rate_service.get_rate(quote_currency, base_currency)
    if inverse_quote is None or inverse_quote.rate == 0:
        return None

    return RateQuote(
        base_currency=base_currency,
        quote_currency=quote_currency,
        rate=1 / inverse_quote.rate,
        provider=inverse_quote.provider,
        source_url=inverse_quote.source_url,
        last_updated=inverse_quote.last_updated,
        next_update=inverse_quote.next_update,
        stale=inverse_quote.stale,
    )


def parse_amount(value: Any) -> float:
    text = str(value or "").strip().replace(" ", "")
    if not text:
        raise ValueError("Introduce una cantidad valida.")

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    amount = float(text)
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("La cantidad debe ser un numero mayor que cero.")
    return amount


def format_amount(value: float, currency_code: str) -> str:
    decimals = 0 if currency_code in WHOLE_NUMBER_CURRENCIES else 2
    return f"{value:,.{decimals}f}"


def format_rate(rate: float) -> str:
    return f"{rate:,.6f}"


def format_history_timestamp(value: str) -> str:
    try:
        dt_value = datetime.fromisoformat(value.replace("Z", ""))
    except ValueError:
        return value
    return dt_value.strftime("%d %b %Y %H:%M UTC")


def get_currency(currency_code: str) -> dict[str, str]:
    currency = CURRENCY_INDEX.get(currency_code)
    if currency is None:
        raise KeyError(f"Unsupported currency: {currency_code}")
    return currency


def normalize_currency_code(value: Any) -> str:
    return str(value or "").strip().upper()


def build_pair_slug(base_currency: str, quote_currency: str) -> str:
    return f"{base_currency.lower()}-{quote_currency.lower()}"


def parse_pair_slug(pair_slug: str) -> tuple[str | None, str | None]:
    parts = pair_slug.split("-", maxsplit=1)
    if len(parts) != 2:
        return None, None
    base_currency = normalize_currency_code(parts[0])
    quote_currency = normalize_currency_code(parts[1])
    if base_currency not in CURRENCY_INDEX or quote_currency not in CURRENCY_INDEX:
        return None, None
    if base_currency == quote_currency:
        return None, None
    return base_currency, quote_currency


def is_valid_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    local_part, _, domain = email.partition("@")
    return bool(local_part and domain and "." in domain)


app = create_app()
handler = app
application = app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
