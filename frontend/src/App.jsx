import { useEffect, useMemo, useState } from "react";

import { cn } from "./lib/cn";

const fallbackCurrencies = [
  { code: "EUR", name: "euro" },
  { code: "USD", name: "dólar estadounidense" },
  { code: "GBP", name: "libra esterlina" },
  { code: "JPY", name: "yen japonés" },
];

function normalizeQuickPair(pair) {
  if (pair.baseCurrency && pair.quoteCurrency) return pair;
  const [baseCurrency = "", quoteCurrency = ""] = (pair.label ?? "").split("/").map((part) => part.trim());
  return { ...pair, baseCurrency, quoteCurrency, label: pair.label ?? `${baseCurrency}/${quoteCurrency}` };
}

function normalizeHistoryItem(item) {
  return {
    amountDisplay: item.amountDisplay ?? item.amount_display,
    baseCurrency: item.baseCurrency ?? item.base_currency,
    quoteCurrency: item.quoteCurrency ?? item.quote_currency,
    convertedAmountDisplay: item.convertedAmountDisplay ?? item.converted_amount_display,
    createdAt: item.createdAt ?? item.created_at,
  };
}

function formatHistoryLabel(item) {
  const normalized = normalizeHistoryItem(item);
  return `${normalized.amountDisplay} ${normalized.baseCurrency} = ${normalized.convertedAmountDisplay} ${normalized.quoteCurrency}`;
}

function SwapIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="swap-icon" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M7 7h11m0 0-3-3m3 3-3 3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M17 17H6m0 0 3 3m-3-3 3-3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Field({ label, children }) {
  return <label className="field"><span>{label}</span>{children}</label>;
}

function Converter({ bootstrap }) {
  const currencies = bootstrap.currencies?.length ? bootstrap.currencies : fallbackCurrencies;
  const quickPairs = (bootstrap.quickPairs ?? []).map(normalizeQuickPair).filter((pair) => pair.baseCurrency && pair.quoteCurrency);
  const [amount, setAmount] = useState(bootstrap.liveSnapshot?.amountDisplay ?? "1");
  const [baseCurrency, setBaseCurrency] = useState(bootstrap.selectedPair?.baseCurrency ?? "EUR");
  const [quoteCurrency, setQuoteCurrency] = useState(bootstrap.selectedPair?.quoteCurrency ?? "USD");
  const [historyItems, setHistoryItems] = useState((bootstrap.historyItems ?? []).map(normalizeHistoryItem));
  const [status, setStatus] = useState({ kind: "idle", message: "Introduce una cantidad y calcularemos el cambio automáticamente." });
  const [shareLabel, setShareLabel] = useState("Compartir resultado");
  const [result, setResult] = useState({
    convertedAmountDisplay: bootstrap.liveSnapshot?.convertedAmountDisplay ?? "—",
    rateDisplay: bootstrap.liveSnapshot?.rateDisplay ?? "—",
    provider: bootstrap.liveSnapshot?.provider ?? "Consultando fuente",
    lastUpdated: bootstrap.liveSnapshot?.lastUpdated ?? "Calculando…",
  });

  const pairHref = `/cambio/${baseCurrency.toLowerCase()}-${quoteCurrency.toLowerCase()}`;
  const selectedBase = useMemo(() => currencies.find((currency) => currency.code === baseCurrency), [currencies, baseCurrency]);
  const selectedQuote = useMemo(() => currencies.find((currency) => currency.code === quoteCurrency), [currencies, quoteCurrency]);

  useEffect(() => {
    if (!amount) {
      setStatus({ kind: "idle", message: "Introduce una cantidad para calcular." });
      return undefined;
    }

    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setStatus({ kind: "loading", message: "Consultando la tasa de referencia…" });
      try {
        const response = await fetch(bootstrap.endpoints?.convert ?? "/convertir", {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ cantidad: amount, moneda_origen: baseCurrency, moneda_destino: quoteCurrency }),
          signal: controller.signal,
        });
        const payload = await response.json();
        if (!response.ok) {
          setStatus({ kind: "error", message: payload.error ?? "No pudimos calcular el cambio." });
          return;
        }

        setResult({
          convertedAmountDisplay: payload.converted_amount_display,
          rateDisplay: payload.rate_display,
          provider: payload.provider,
          lastUpdated: payload.last_updated,
        });
        setStatus({
          kind: payload.stale ? "warning" : "success",
          message: payload.stale ? "Mostramos la última tasa disponible." : "Tasa de referencia actualizada.",
        });

        const historyResponse = await fetch(`${bootstrap.endpoints?.history ?? "/historial"}?limite=${bootstrap.historyLimit ?? 6}`, {
          headers: { Accept: "application/json" }, signal: controller.signal,
        });
        if (historyResponse.ok) setHistoryItems((await historyResponse.json()).map(normalizeHistoryItem));
      } catch (error) {
        if (error.name !== "AbortError") setStatus({ kind: "error", message: "No pudimos conectar con la fuente de tasas." });
      }
    }, 350);

    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [amount, baseCurrency, quoteCurrency, bootstrap.endpoints, bootstrap.historyLimit]);

  const swapPair = () => {
    setBaseCurrency(quoteCurrency);
    setQuoteCurrency(baseCurrency);
  };

  const shareResult = async () => {
    const text = `${amount || "0"} ${baseCurrency} = ${result.convertedAmountDisplay} ${quoteCurrency} · Tu Cambio`;
    const url = new URL(pairHref, window.location.origin).toString();
    try {
      if (navigator.share) await navigator.share({ title: "Tu Cambio", text, url });
      else await navigator.clipboard.writeText(`${text} · ${url}`);
      setShareLabel("¡Resultado listo!");
      window.setTimeout(() => setShareLabel("Compartir resultado"), 1800);
    } catch (error) {
      if (error.name !== "AbortError") setShareLabel("No se pudo compartir");
    }
  };

  return (
    <section className="converter-card" id="calculadora" aria-labelledby="converter-title">
      <div className="converter-header">
        <div>
          <p className="eyebrow">Tipo de cambio de referencia</p>
          <h1 id="converter-title">{bootstrap.seoContent?.heading ?? "Conversor de divisas rápido y gratuito"}</h1>
          <p>{bootstrap.seoContent?.intro ?? "Elige dos monedas, escribe una cantidad y consulta el resultado."}</p>
        </div>
        <div className="trust-badge"><strong>Gratis</strong><span>Sin cuenta ni registro</span></div>
      </div>

      <div className="converter-layout">
        <div className="form-panel">
          <div className={cn("status", status.kind)} role="status">{status.message}</div>
          <Field label={`Cantidad en ${baseCurrency}`}>
            <input value={amount} onChange={(event) => setAmount(event.target.value)} inputMode="decimal" autoComplete="off" aria-label={`Cantidad en ${baseCurrency}`} />
          </Field>
          <div className="currency-row">
            <Field label="De">
              <select value={baseCurrency} onChange={(event) => setBaseCurrency(event.target.value)} aria-label="Moneda de origen">
                {currencies.map((currency) => <option key={currency.code} value={currency.code}>{currency.code} · {currency.name}</option>)}
              </select>
            </Field>
            <button type="button" onClick={swapPair} className="swap-button" aria-label="Invertir monedas"><SwapIcon /></button>
            <Field label="A">
              <select value={quoteCurrency} onChange={(event) => setQuoteCurrency(event.target.value)} aria-label="Moneda de destino">
                {currencies.map((currency) => <option key={currency.code} value={currency.code}>{currency.code} · {currency.name}</option>)}
              </select>
            </Field>
          </div>
          {!!quickPairs.length && (
            <div className="quick-pairs"><span>Conversiones populares</span><div>
              {quickPairs.slice(0, 8).map((pair) => <a key={`${pair.baseCurrency}-${pair.quoteCurrency}`} href={pair.href}>{pair.label}</a>)}
            </div></div>
          )}
        </div>

        <div className="result-panel" aria-live="polite">
          <span className="result-label">{amount || "0"} {baseCurrency} equivale aproximadamente a</span>
          <div className="result-value">{result.convertedAmountDisplay}<small>{quoteCurrency}</small></div>
          <dl className="result-details">
            <div><dt>1 {baseCurrency} equivale a</dt><dd>{result.rateDisplay} {quoteCurrency}</dd></div>
            <div><dt>Fuente</dt><dd>{result.provider}</dd></div>
            <div><dt>Actualización</dt><dd>{result.lastUpdated}</dd></div>
          </dl>
          <div className="result-actions">
            <button type="button" className="primary-action" onClick={shareResult}>{shareLabel}</button>
            {baseCurrency !== quoteCurrency && <a href={pairHref}>Ver página {baseCurrency}/{quoteCurrency}</a>}
          </div>
        </div>
      </div>

      {!!historyItems.length && (
        <div className="history-panel">
          <div><h2>Conversiones recientes</h2><p>Los últimos cálculos de esta sesión de servicio.</p></div>
          <div className="history-list">{historyItems.slice(0, 5).map((item) => (
            <div key={`${item.baseCurrency}-${item.quoteCurrency}-${item.createdAt}`} className="history-item"><strong>{formatHistoryLabel(item)}</strong><span>{item.createdAt}</span></div>
          ))}</div>
        </div>
      )}

      <p className="disclaimer">El resultado es informativo. {selectedBase?.name ?? baseCurrency} y {selectedQuote?.name ?? quoteCurrency} pueden tener precios distintos en bancos, tarjetas y casas de cambio.</p>
    </section>
  );
}

function ValueSection({ bootstrap }) {
  return (
    <section className="info-section" aria-labelledby="benefits-title">
      <div><p className="eyebrow">Hecho para decidir mejor</p><h2 id="benefits-title">Una cifra clara, con la tasa y la fuente a la vista.</h2></div>
      <div className="metric-grid">
        <div><strong>{bootstrap.metrics?.currencies ?? bootstrap.currencies?.length ?? 0}+</strong><span>monedas disponibles</span></div>
        <div><strong>0 €</strong><span>coste de uso</span></div>
        <div><strong>24/7</strong><span>acceso desde cualquier dispositivo</span></div>
      </div>
    </section>
  );
}

function SeoContent({ bootstrap }) {
  const content = bootstrap.seoContent ?? {};
  const quickPairs = (bootstrap.quickPairs ?? []).map(normalizeQuickPair);
  return (
    <>
      <section className="content-section steps-section" id="como-funciona">
        <p className="eyebrow">Cómo funciona</p><h2>Convierte {content.baseCode} a {content.quoteCode} en tres pasos</h2>
        <div className="steps-grid">
          <article><span>1</span><h3>Escribe la cantidad</h3><p>Admite números enteros y decimales con punto o coma.</p></article>
          <article><span>2</span><h3>Elige las monedas</h3><p>Selecciona la moneda de origen y la de destino, o inviértelas con un toque.</p></article>
          <article><span>3</span><h3>Revisa la referencia</h3><p>Consulta el total estimado, la tasa aplicada, la fuente y su actualización.</p></article>
        </div>
      </section>

      <section className="content-section split-content">
        <div><p className="eyebrow">Útil en el día a día</p><h2>Para viajes, compras, presupuestos y remesas</h2></div>
        <div className="prose"><p>Tu Cambio ayuda a comparar importes antes de pagar en otra moneda, preparar un presupuesto de viaje o estimar cuánto podría recibir otra persona.</p><p>La cifra es una referencia, no una oferta de compra o venta. Contrasta el resultado con la entidad que procesará tu operación y revisa sus comisiones.</p></div>
      </section>

      <section className="content-section" id="preguntas">
        <p className="eyebrow">Preguntas frecuentes</p><h2>Todo lo que debes saber sobre esta conversión</h2>
        <div className="faq-grid">{(content.faqItems ?? []).map((item) => (
          <article key={item.question}><h3>{item.question}</h3><p>{item.answer}</p></article>
        ))}</div>
      </section>

      <section className="content-section related-section">
        <div><p className="eyebrow">Explora otros cambios</p><h2>Conversiones populares</h2></div>
        <div className="quick-link-list">{quickPairs.map((pair) => (
          <a key={pair.href} href={pair.href}><span>{pair.description}</span><strong>{pair.label}</strong></a>
        ))}</div>
      </section>
    </>
  );
}

export default function App({ bootstrap = {} }) {
  return (
    <div className="app-shell">
      <header className="site-header">
        <a href="/" className="brand" aria-label="Tu Cambio, inicio"><span>TC</span>{bootstrap.appName ?? "Tu Cambio"}</a>
        <nav className="top-nav" aria-label="Navegación principal"><a href="#calculadora">Calculadora</a><a href="#como-funciona">Cómo funciona</a><a href="#preguntas">Preguntas</a></nav>
      </header>
      <main><Converter bootstrap={bootstrap} /><ValueSection bootstrap={bootstrap} /><SeoContent bootstrap={bootstrap} /></main>
      <footer className="site-footer"><div><strong>{bootstrap.appName ?? "Tu Cambio"}</strong><span>Conversor gratuito de tipos de cambio de referencia.</span></div><nav aria-label="Enlaces del pie"><a href="/robots.txt">Robots</a><a href="/sitemap.xml">Sitemap</a></nav></footer>
    </div>
  );
}
