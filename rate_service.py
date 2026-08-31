from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class RateQuote:
    base_currency: str
    quote_currency: str
    rate: float
    provider: str
    source_url: str
    last_updated: str | None
    next_update: str | None
    stale: bool


class RateService:
    def __init__(
        self,
        *,
        ttl_seconds: int = 900,
        timeout_seconds: float = 5.0,
        session: requests.Session | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get_rate(self, base_currency: str, quote_currency: str) -> RateQuote | None:
        cached_payload = self._get_cached_payload(base_currency)
        if cached_payload is not None:
            quote = self._build_quote(cached_payload, base_currency, quote_currency, stale=False)
            if quote is not None:
                return quote

        stale_payload = self._get_any_payload(base_currency)
        fresh_payload = self._fetch_payload(base_currency)
        if fresh_payload is not None:
            with self._lock:
                self._cache[base_currency] = fresh_payload
            quote = self._build_quote(fresh_payload, base_currency, quote_currency, stale=False)
            if quote is not None:
                return quote

        if stale_payload is not None:
            return self._build_quote(stale_payload, base_currency, quote_currency, stale=True)
        return None

    def _fetch_payload(self, base_currency: str) -> dict[str, Any] | None:
        url = f"https://open.er-api.com/v6/latest/{base_currency}"
        try:
            response = self.session.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            return None

        if payload.get("result") != "success" or "rates" not in payload:
            return None

        return {
            "base_currency": base_currency,
            "rates": payload["rates"],
            "provider": "ExchangeRate-API",
            "source_url": payload.get("documentation", url),
            "last_updated": payload.get("time_last_update_utc"),
            "next_update": payload.get("time_next_update_utc"),
            "fetched_at": time.time(),
        }

    def _get_cached_payload(self, base_currency: str) -> dict[str, Any] | None:
        payload = self._get_any_payload(base_currency)
        if payload is None:
            return None
        if time.time() - payload["fetched_at"] <= self.ttl_seconds:
            return payload
        return None

    def _get_any_payload(self, base_currency: str) -> dict[str, Any] | None:
        with self._lock:
            return self._cache.get(base_currency)

    def _build_quote(
        self,
        payload: dict[str, Any],
        base_currency: str,
        quote_currency: str,
        *,
        stale: bool,
    ) -> RateQuote | None:
        rate = payload["rates"].get(quote_currency)
        if rate is None:
            return None

        return RateQuote(
            base_currency=base_currency,
            quote_currency=quote_currency,
            rate=float(rate),
            provider=str(payload.get("provider", "ExchangeRate-API")),
            source_url=str(payload.get("source_url", "")),
            last_updated=payload.get("last_updated"),
            next_update=payload.get("next_update"),
            stale=stale,
        )
