import tempfile
import unittest
from pathlib import Path

from app import create_app
from rate_service import RateQuote


class FakeRateService:
    def __init__(self):
        self.calls = []

    def get_rate(self, base_currency, quote_currency):
        self.calls.append((base_currency, quote_currency))
        rates = {
            ("EUR", "USD"): 1.2,
            ("USD", "MXN"): 17.1,
            ("USD", "EUR"): 0.8,
        }
        rate = rates.get((base_currency, quote_currency))
        if rate is None:
            return None
        return RateQuote(
            base_currency=base_currency,
            quote_currency=quote_currency,
            rate=rate,
            provider="Fake Provider",
            source_url="https://example.com/rates",
            last_updated="Mon, 20 Apr 2026 00:00:00 +0000",
            next_update="Tue, 21 Apr 2026 00:00:00 +0000",
            stale=False,
        )


class TuCambioAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "test.db"
        self.rate_service = FakeRateService()
        self.app = create_app(
            {
                "TESTING": True,
                "DATABASE_PATH": database_path,
                "RATE_SERVICE": self.rate_service,
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_homepage_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Tu Cambio", response.data)
        self.assertIn(b'id="root"', response.data)
        self.assertIn(b"bootstrap-data", response.data)
        self.assertIn(b"Conversor de divisas y tipos de cambio", response.data)
        self.assertIn(b"FAQPage", response.data)
        self.assertIn(b"rel=\"canonical\" href=\"https://tu-cambio.vercel.app/\"", response.data)
        self.assertEqual(self.rate_service.calls, [], "La portada no debe bloquearse esperando una API externa")

    def test_pair_page_renders(self):
        response = self.client.get("/cambio/usd-mxn")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"USD", response.data)
        self.assertIn(b"MXN", response.data)
        self.assertIn(b'"pairSlug": "usd-mxn"', response.data)
        self.assertIn(b"Convertir d\xc3\xb3lar estadounidense a peso mexicano", response.data)
        self.assertIn(b"BreadcrumbList", response.data)

    def test_sitemap_uses_production_canonicals_and_selected_pairs(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"https://tu-cambio.vercel.app/cambio/usd-mxn", response.data)
        self.assertNotIn(b"localhost", response.data)
        self.assertLess(response.data.count(b"<url>"), 150)

    def test_robots_blocks_action_endpoints(self):
        response = self.client.get("/robots.txt")
        self.assertIn(b"Disallow: /convertir", response.data)
        self.assertIn(b"Sitemap: https://tu-cambio.vercel.app/sitemap.xml", response.data)

    def test_convert_endpoint_returns_payload(self):
        response = self.client.post(
            "/convertir",
            json={
                "cantidad": "100",
                "moneda_origen": "EUR",
                "moneda_destino": "USD",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["converted_amount_display"], "120.00")
        self.assertEqual(payload["rate_display"], "1.200000")

        history_response = self.client.get("/historial")
        self.assertEqual(history_response.status_code, 200)
        self.assertEqual(history_response.get_json()[0]["base_currency"], "EUR")

    def test_convert_endpoint_rejects_invalid_currency(self):
        response = self.client.post(
            "/convertir",
            json={
                "cantidad": "100",
                "moneda_origen": "EUR",
                "moneda_destino": "ZZZ",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_alert_subscription_is_idempotent(self):
        first_response = self.client.post(
            "/suscribirse-alertas",
            json={
                "email": "test@example.com",
                "moneda_origen": "USD",
                "moneda_destino": "MXN",
            },
        )
        second_response = self.client.post(
            "/suscribirse-alertas",
            json={
                "email": "test@example.com",
                "moneda_origen": "USD",
                "moneda_destino": "MXN",
            },
        )
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertIn("Ya estabas", second_response.get_json()["message"])

    def test_google_verification_route(self):
        response = self.client.get("/google91d8c072ad165708.html")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"google-site-verification: google91d8c072ad165708.html", response.data)

    def test_ads_txt_route(self):
        response = self.client.get("/ads.txt")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
