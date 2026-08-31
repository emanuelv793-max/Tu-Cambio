from __future__ import annotations


CURRENCIES = [
    {"code": "EUR", "name": "euro", "region": "la eurozona", "flag_url": "https://flagcdn.com/eu.svg"},
    {"code": "USD", "name": "dólar estadounidense", "region": "Estados Unidos y mercados internacionales", "flag_url": "https://flagcdn.com/us.svg"},
    {"code": "VES", "name": "bolívar venezolano", "region": "Venezuela", "flag_url": "https://flagcdn.com/ve.svg"},
    {"code": "COP", "name": "peso colombiano", "region": "Colombia", "flag_url": "https://flagcdn.com/co.svg"},
    {"code": "MXN", "name": "peso mexicano", "region": "México", "flag_url": "https://flagcdn.com/mx.svg"},
    {"code": "ARS", "name": "peso argentino", "region": "Argentina", "flag_url": "https://flagcdn.com/ar.svg"},
    {"code": "CLP", "name": "peso chileno", "region": "Chile", "flag_url": "https://flagcdn.com/cl.svg"},
    {"code": "BRL", "name": "real brasileño", "region": "Brasil", "flag_url": "https://flagcdn.com/br.svg"},
    {"code": "PEN", "name": "sol peruano", "region": "Perú", "flag_url": "https://flagcdn.com/pe.svg"},
    {"code": "PYG", "name": "guaraní paraguayo", "region": "Paraguay", "flag_url": "https://flagcdn.com/py.svg"},
    {"code": "UYU", "name": "peso uruguayo", "region": "Uruguay", "flag_url": "https://flagcdn.com/uy.svg"},
    {"code": "BOB", "name": "boliviano", "region": "Bolivia", "flag_url": "https://flagcdn.com/bo.svg"},
    {"code": "CRC", "name": "colón costarricense", "region": "Costa Rica", "flag_url": "https://flagcdn.com/cr.svg"},
    {"code": "DOP", "name": "peso dominicano", "region": "República Dominicana", "flag_url": "https://flagcdn.com/do.svg"},
    {"code": "GTQ", "name": "quetzal guatemalteco", "region": "Guatemala", "flag_url": "https://flagcdn.com/gt.svg"},
    {"code": "HNL", "name": "lempira hondureño", "region": "Honduras", "flag_url": "https://flagcdn.com/hn.svg"},
    {"code": "NIO", "name": "córdoba nicaragüense", "region": "Nicaragua", "flag_url": "https://flagcdn.com/ni.svg"},
    {"code": "PAB", "name": "balboa panameño", "region": "Panamá", "flag_url": "https://flagcdn.com/pa.svg"},
    {"code": "GBP", "name": "libra esterlina", "region": "Reino Unido", "flag_url": "https://flagcdn.com/gb.svg"},
    {"code": "CHF", "name": "franco suizo", "region": "Suiza y Liechtenstein", "flag_url": "https://flagcdn.com/ch.svg"},
    {"code": "CAD", "name": "dólar canadiense", "region": "Canadá", "flag_url": "https://flagcdn.com/ca.svg"},
    {"code": "AUD", "name": "dólar australiano", "region": "Australia", "flag_url": "https://flagcdn.com/au.svg"},
    {"code": "NZD", "name": "dólar neozelandés", "region": "Nueva Zelanda", "flag_url": "https://flagcdn.com/nz.svg"},
    {"code": "JPY", "name": "yen japonés", "region": "Japón", "flag_url": "https://flagcdn.com/jp.svg"},
    {"code": "CNY", "name": "yuan chino", "region": "China", "flag_url": "https://flagcdn.com/cn.svg"},
    {"code": "INR", "name": "rupia india", "region": "India", "flag_url": "https://flagcdn.com/in.svg"},
    {"code": "KRW", "name": "won surcoreano", "region": "Corea del Sur", "flag_url": "https://flagcdn.com/kr.svg"},
    {"code": "AED", "name": "dírham de Emiratos", "region": "Emiratos Árabes Unidos", "flag_url": "https://flagcdn.com/ae.svg"},
    {"code": "TRY", "name": "lira turca", "region": "Turquía", "flag_url": "https://flagcdn.com/tr.svg"},
    {"code": "PLN", "name": "esloti polaco", "region": "Polonia", "flag_url": "https://flagcdn.com/pl.svg"},
    {"code": "SEK", "name": "corona sueca", "region": "Suecia", "flag_url": "https://flagcdn.com/se.svg"},
]

CURRENCY_INDEX = {currency["code"]: currency for currency in CURRENCIES}
DEFAULT_BASE_CURRENCY = "EUR"
DEFAULT_QUOTE_CURRENCY = "USD"

FEATURED_PAIRS = [
    ("EUR", "USD"), ("USD", "EUR"), ("USD", "VES"), ("USD", "COP"),
    ("USD", "MXN"), ("USD", "ARS"), ("EUR", "GBP"), ("USD", "BRL"),
    ("USD", "PEN"), ("EUR", "CHF"),
]


def build_indexable_pairs() -> tuple[tuple[str, str], ...]:
    """Build a focused crawl set instead of flooding search engines with thin URLs."""
    pairs = set(FEATURED_PAIRS)
    for currency in CURRENCIES:
        code = currency["code"]
        if code not in {"USD", "EUR"}:
            pairs.update({("USD", code), (code, "USD"), ("EUR", code), (code, "EUR")})
    return tuple(sorted(pairs))


INDEXABLE_PAIRS = build_indexable_pairs()
