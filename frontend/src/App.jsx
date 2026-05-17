import { useEffect, useState } from "react";

import { cn } from "./lib/cn";

const fallbackCurrencies = [
  { code: "EUR", name: "Euro" },
  { code: "USD", name: "Dolar estadounidense" },
  { code: "GBP", name: "Libra esterlina" },
  { code: "JPY", name: "Yen japones" },
];

function normalizeQuickPair(pair) {
  if (pair.baseCurrency && pair.quoteCurrency) {
    return pair;
  }

  const [baseCurrency = "", quoteCurrency = ""] = (pair.label ?? "").split("/").map((part) => part.trim());
  return {
    ...pair,
    baseCurrency,
    quoteCurrency,
    label: pair.label ?? `${baseCurrency}/${quoteCurrency}`,
  };
}

function normalizeHistoryItem(item) {
  return {
    amountDisplay: item.amountDisplay ?? item.amount_display,
    baseCurrency: item.baseCurrency ?? item.base_currency,
    quoteCurrency: item.quoteCurrency ?? item.quote_currency,
    convertedAmountDisplay: item.convertedAmountDisplay ?? item.converted_amount_display,
    provider: item.provider,
    createdAt: item.createdAt ?? item.created_at,
  };
}

function formatHistoryLabel(item) {
  const normalized = normalizeHistoryItem(item);
  return `${normalized.amountDisplay} ${normalized.baseCurrency} = ${normalized.convertedAmountDisplay} ${normalized.quoteCurrency}`;
}

function SwapIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M7 7h11m0 0-3-3m3 3-3 3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M17 17H6m0 0 3 3m-3-3 3-3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function Converter({ bootstrap }) {
  const currencies = bootstrap.currencies?.length ? bootstrap.currencies : fallbackCurrencies;
  const quickPairs = (bootstrap.quickPairs ?? []).map(normalizeQuickPair).filter((pair) => pair.baseCurrency && pair.quoteCurrency);
  const [amount, setAmount] = useState(bootstrap.liveSnapshot?.amountDisplay ?? "1.00");
  const [baseCurrency, setBaseCurrency] = useState(bootstrap.selectedPair?.baseCurrency ?? "EUR");
  const [quoteCurrency, setQuoteCurrency] = useState(bootstrap.selectedPair?.quoteCurrency ?? "USD");
  const [historyItems, setHistoryItems] = useState((bootstrap.historyItems ?? []).map(normalizeHistoryItem));
  const [status, setStatus] = useState({ kind: "idle", message: "Introduce una cantidad y el cambio se calcula solo." });
  const [result, setResult] = useState({
    convertedAmountDisplay: bootstrap.liveSnapshot?.convertedAmountDisplay ?? "1.17",
    rateDisplay: bootstrap.liveSnapshot?.rateDisplay ?? "1.174959",
    provider: bootstrap.liveSnapshot?.provider ?? "Fuente en vivo",
    lastUpdated: bootstrap.liveSnapshot?.lastUpdated ?? "Actualizado ahora",
  });

  useEffect(() => {
    if (!amount) {
      setStatus({ kind: "idle", message: "Introduce una cantidad para calcular." });
      return undefined;
    }

    const timer = window.setTimeout(async () => {
      setStatus({ kind: "loading", message: "Calculando..." });

      try {
        const response = await fetch(bootstrap.endpoints?.convert ?? "/convertir", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            cantidad: amount,
            moneda_origen: baseCurrency,
            moneda_destino: quoteCurrency,
          }),
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
          message: payload.stale ? "Usando la ultima tasa disponible." : "Cambio actualizado.",
        });

        const historyResponse = await fetch(`${bootstrap.endpoints?.history ?? "/historial"}?limite=${bootstrap.historyLimit ?? 6}`, {
          headers: { Accept: "application/json" },
        });

        if (historyResponse.ok) {
          const historyPayload = await historyResponse.json();
          setHistoryItems(historyPayload.map(normalizeHistoryItem));
        }
      } catch (error) {
        setStatus({ kind: "error", message: "No pudimos conectar con el servidor." });
      }
    }, 250);

    return () => window.clearTimeout(timer);
  }, [amount, baseCurrency, quoteCurrency, bootstrap.endpoints, bootstrap.historyLimit]);

  const swapPair = () => {
    setBaseCurrency(quoteCurrency);
    setQuoteCurrency(baseCurrency);
  };

  const applyPair = (base, quote) => {
    setBaseCurrency(base);
    setQuoteCurrency(quote);
  };

  return (
    <section className="converter-card" aria-labelledby="converter-title">
      <div className="converter-header">
        <div>
          <p className="eyebrow">Conversor de divisas</p>
          <h1 id="converter-title">Calcula el cambio al instante</h1>
          <p>Escribe una cantidad, elige las monedas y revisa el resultado con la tasa usada.</p>
        </div>
      </div>

      <div className="converter-layout">
        <div className="form-panel">
          <div className={cn("status", status.kind)}>{status.message}</div>

          <Field label="Cantidad">
            <input value={amount} onChange={(event) => setAmount(event.target.value)} inputMode="decimal" aria-label="Cantidad" />
          </Field>

          <div className="currency-row">
            <Field label="De">
              <select value={baseCurrency} onChange={(event) => setBaseCurrency(event.target.value)} aria-label="Moneda de origen">
                {currencies.map((currency) => (
                  <option key={currency.code} value={currency.code}>
                    {currency.code} - {currency.name}
                  </option>
                ))}
              </select>
            </Field>

            <button type="button" onClick={swapPair} className="swap-button" aria-label="Invertir monedas">
              <SwapIcon />
            </button>

            <Field label="A">
              <select value={quoteCurrency} onChange={(event) => setQuoteCurrency(event.target.value)} aria-label="Moneda de destino">
                {currencies.map((currency) => (
                  <option key={currency.code} value={currency.code}>
                    {currency.code} - {currency.name}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          {!!quickPairs.length && (
            <div className="quick-pairs">
              <span>Pares comunes</span>
              <div>
                {quickPairs.slice(0, 6).map((pair) => (
                  <button key={`${pair.baseCurrency}-${pair.quoteCurrency}`} type="button" onClick={() => applyPair(pair.baseCurrency, pair.quoteCurrency)}>
                    {pair.label ?? `${pair.baseCurrency}/${pair.quoteCurrency}`}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="result-panel" aria-live="polite">
          <span className="result-label">
            {amount || "0"} {baseCurrency} equivale a
          </span>
          <div className="result-value">
            {result.convertedAmountDisplay}
            <small>{quoteCurrency}</small>
          </div>
          <dl className="result-details">
            <div>
              <dt>Tasa</dt>
              <dd>{result.rateDisplay}</dd>
            </div>
            <div>
              <dt>Fuente</dt>
              <dd>{result.provider}</dd>
            </div>
            <div>
              <dt>Actualizado</dt>
              <dd>{result.lastUpdated}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="history-panel">
        <div>
          <h2>Conversiones recientes</h2>
          <p>Un resumen corto de los ultimos calculos hechos en esta app.</p>
        </div>
        <div className="history-list">
          {historyItems.slice(0, 5).map((item) => (
            <div key={`${item.baseCurrency}-${item.quoteCurrency}-${item.createdAt}`} className="history-item">
              <strong>{formatHistoryLabel(item)}</strong>
              <span>{item.createdAt}</span>
            </div>
          ))}
          {!historyItems.length && <div className="history-item empty">Todavia no hay conversiones guardadas.</div>}
        </div>
      </div>
    </section>
  );
}

function InfoSection({ bootstrap }) {
  const metrics = [
    ["Divisas disponibles", bootstrap.metrics?.currencies ?? bootstrap.currencies?.length ?? 0],
    ["Pares sugeridos", bootstrap.quickPairs?.length ?? 0],
    ["Historial visible", bootstrap.metrics?.history ?? bootstrap.historyItems?.length ?? 0],
  ];

  return (
    <section className="info-section">
      <div>
        <p className="eyebrow">Simple y ordenado</p>
        <h2>Todo lo necesario para revisar un cambio sin distracciones.</h2>
      </div>
      <div className="metric-grid">
        {metrics.map(([label, value]) => (
          <div key={label}>
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function App({ bootstrap = {} }) {
  return (
    <div className="app-shell">
      <header className="site-header">
        <a href="/" className="brand">
          <span>TC</span>
          {bootstrap.appName ?? "Tu Cambio"}
        </a>
      </header>

      <main>
        <Converter bootstrap={bootstrap} />
        <InfoSection bootstrap={bootstrap} />
      </main>

      <footer className="site-footer">
        <span>{bootstrap.appName ?? "Tu Cambio"}</span>
        <span>Conversor de divisas rapido y sencillo.</span>
      </footer>
    </div>
  );
}
