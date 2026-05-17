from __future__ import annotations


CURRENCIES = [
    {"code": "EUR", "name": "Euro", "flag_url": "https://flagcdn.com/eu.svg"},
    {"code": "USD", "name": "Dolar estadounidense", "flag_url": "https://flagcdn.com/us.svg"},
    {"code": "VES", "name": "Bolivar venezolano", "flag_url": "https://flagcdn.com/ve.svg"},
    {"code": "PYG", "name": "Guarani paraguayo", "flag_url": "https://flagcdn.com/py.svg"},
    {"code": "ARS", "name": "Peso argentino", "flag_url": "https://flagcdn.com/ar.svg"},
    {"code": "MXN", "name": "Peso mexicano", "flag_url": "https://flagcdn.com/mx.svg"},
    {"code": "CLP", "name": "Peso chileno", "flag_url": "https://flagcdn.com/cl.svg"},
    {"code": "COP", "name": "Peso colombiano", "flag_url": "https://flagcdn.com/co.svg"},
    {"code": "BRL", "name": "Real brasileno", "flag_url": "https://flagcdn.com/br.svg"},
    {"code": "GBP", "name": "Libra esterlina", "flag_url": "https://flagcdn.com/gb.svg"},
    {"code": "JPY", "name": "Yen japones", "flag_url": "https://flagcdn.com/jp.svg"},
    {"code": "CAD", "name": "Dolar canadiense", "flag_url": "https://flagcdn.com/ca.svg"},
    {"code": "AUD", "name": "Dolar australiano", "flag_url": "https://flagcdn.com/au.svg"},
    {"code": "CHF", "name": "Franco suizo", "flag_url": "https://flagcdn.com/ch.svg"},
    {"code": "CNY", "name": "Yuan chino", "flag_url": "https://flagcdn.com/cn.svg"},
    {"code": "SEK", "name": "Corona sueca", "flag_url": "https://flagcdn.com/se.svg"},
]

CURRENCY_INDEX = {currency["code"]: currency for currency in CURRENCIES}
DEFAULT_BASE_CURRENCY = "EUR"
DEFAULT_QUOTE_CURRENCY = "USD"
FEATURED_PAIRS = [
    ("EUR", "USD"),
    ("USD", "EUR"),
    ("USD", "VES"),
    ("EUR", "VES"),
    ("USD", "MXN"),
    ("USD", "COP"),
    ("EUR", "ARS"),
    ("USD", "BRL"),
]
