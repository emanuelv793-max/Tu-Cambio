# Tu Cambio

Conversor de divisas en español construido con Flask, React y Vite. La aplicación ofrece más de 30 monedas, páginas indexables para pares relevantes y tipos de cambio de referencia mediante ExchangeRate-API.

## Desarrollo local

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm install
npm run build
.\.venv\Scripts\python.exe app.py
```

La web queda disponible en `http://127.0.0.1:5000`.

## Variables de entorno

- `PUBLIC_BASE_URL`: dominio canónico, por defecto `https://tu-cambio.vercel.app`.
- `RATE_CACHE_TTL_SECONDS`: duración de la caché de tasas, por defecto 900 segundos.
- `RATE_REQUEST_TIMEOUT_SECONDS`: tiempo máximo de espera a la fuente, por defecto 5 segundos.
- `DATABASE_PATH`: ruta opcional para el historial y las suscripciones.

## SEO técnico

- HTML inicial con contenido útil aunque JavaScript todavía no se haya ejecutado.
- Títulos, descripciones y canonical únicos por par de monedas.
- JSON-LD de `WebSite`, `WebApplication`, `FAQPage` y breadcrumbs.
- Sitemap limitado a pares con demanda potencial para evitar contenido indexable masivo y débil.
- Enlaces internos rastreables, `robots.txt`, PWA y caché CDN.
- La respuesta HTML no espera a la API de tasas; el cálculo se completa en el navegador.

## Verificación

```powershell
npm run build
python -m unittest discover -s tests -v
```

Después de desplegar, envía `https://tu-cambio.vercel.app/sitemap.xml` a Google Search Console y Bing Webmaster Tools. El posicionamiento depende también de autoridad, menciones, enlaces relevantes y contenido editorial; ningún cambio técnico garantiza una posición concreta.
