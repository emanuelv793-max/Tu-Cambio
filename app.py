from __future__ import annotations

import math
import os
from datetime import datetime, timezone
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

from currencies import CURRENCIES, CURRENCY_INDEX, DEFAULT_BASE_CURRENCY, DEFAULT_QUOTE_CURRENCY, FEATURED_PAIRS
from database import fetch_recent_history, init_db, record_conversion, register_alert_subscription
from rate_service import RateQuote, RateService

WHOLE_NUMBER_CURRENCIES = {"JPY", "PYG", "VES"}
DEFAULT_HISTORY_LIMIT = 6


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        APP_NAME="Tu Cambio",
        DATABASE_PATH=Path(os.environ.get("DATABASE_PATH", "historial.db")),
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
        sitemap_url = url_for("sitemap", _external=True)
        response = make_response(f"User-agent: *\nAllow: /\nSitemap: {sitemap_url}\n")
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        return response

    @app.route("/sitemap.xml")
    def sitemap():
        namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
        urlset = Element("urlset", xmlns=namespace)

        urls = [url_for("home", _external=True)]
        for base_currency in CURRENCIES:
            for quote_currency in CURRENCIES:
                if base_currency["code"] == quote_currency["code"]:
                    continue
                urls.append(
                    url_for(
                        "pair_page",
                        pair_slug=build_pair_slug(base_currency["code"], quote_currency["code"]),
                        _external=True,
                    )
                )

        last_modified = datetime.now(timezone.utc).date().isoformat()
        for location in urls:
            url_node = SubElement(urlset, "url")
            SubElement(url_node, "loc").text = location
            SubElement(url_node, "lastmod").text = last_modified

        response = make_response(tostring(urlset, encoding="unicode"))
        response.headers["Content-Type"] = "application/xml; charset=utf-8"
        return response

    @app.route("/ads.txt")
    def ads():
        ads_file = Path(app.root_path) / "ads.txt"
        if not ads_file.exists():
            abort(404)
        return send_from_directory(app.root_path, "ads.txt")

    return app


def render_pair_page(base_currency: str, quote_currency: str, canonical_home: bool = False):
    initial_amount = 1.0
    initial_conversion = build_same_currency_payload(initial_amount, base_currency)
    if base_currency != quote_currency:
        rate_quote = resolve_rate_quote(base_currency, quote_currency)
        if rate_quote is not None:
            initial_conversion = build_conversion_payload(
                initial_amount,
                base_currency,
                quote_currency,
                rate_quote,
            )

    base_details = get_currency(base_currency)
    quote_details = get_currency(quote_currency)
    pair_label = f"{base_details['name']} a {quote_details['name']}"
    canonical_url = (
        url_for(
            "home" if canonical_home else "pair_page",
            pair_slug=build_pair_slug(base_currency, quote_currency),
            _external=True,
        )
        if not canonical_home
        else url_for("home", _external=True)
    )
    quick_pairs = [
        {
            "label": f"{get_currency(base)['code']} / {get_currency(quote)['code']}",
            "description": f"{get_currency(base)['name']} a {get_currency(quote)['name']}",
            "href": url_for("pair_page", pair_slug=build_pair_slug(base, quote)),
            "active": base == base_currency and quote == quote_currency,
        }
        for base, quote in FEATURED_PAIRS
    ]

    history_items = get_history_payload()

    seo_schema = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "Tu Cambio",
        "applicationCategory": "FinanceApplication",
        "operatingSystem": "Any",
        "description": f"Conversor sencillo para revisar {pair_label.lower()} con tasa actualizada.",
        "url": canonical_url,
    }

    bootstrap_data = {
        "appName": current_app.config["APP_NAME"],
        "currencies": CURRENCIES,
        "selectedPair": {
            "baseCurrency": base_currency,
            "quoteCurrency": quote_currency,
            "pairLabel": pair_label,
            "pairSlug": build_pair_slug(base_currency, quote_currency),
            "baseName": base_details["name"],
            "quoteName": quote_details["name"],
        },
        "liveSnapshot": {
            "amountDisplay": initial_conversion["amount_display"],
            "convertedAmountDisplay": initial_conversion["converted_amount_display"],
            "rateDisplay": initial_conversion["rate_display"],
            "provider": initial_conversion["provider"],
            "lastUpdated": initial_conversion["last_updated"],
            "nextUpdate": initial_conversion["next_update"],
        },
        "quickPairs": quick_pairs,
        "historyItems": [
            {
                "amountDisplay": item["amount_display"],
                "baseCurrency": item["base_currency"],
                "quoteCurrency": item["quote_currency"],
                "convertedAmountDisplay": item["converted_amount_display"],
                "provider": item["provider"],
                "createdAt": item["created_at"],
                "stale": item["stale"],
            }
            for item in history_items
        ],
        "metrics": {
            "currencies": len(CURRENCIES),
            "featuredPairs": len(FEATURED_PAIRS),
            "history": len(history_items),
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
        page_title=f"{pair_label} | Conversor de divisas | Tu Cambio",
        page_description=f"Calcula {pair_label.lower()} al instante con una app sencilla, clara y rapida.",
        canonical_url=canonical_url,
        seo_schema=seo_schema,
        bootstrap_data=bootstrap_data,
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
