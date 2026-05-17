const stateElement = document.getElementById("app-state");

if (stateElement) {
  const appState = JSON.parse(stateElement.textContent);
  const currencies = Object.fromEntries(appState.currencies.map((currency) => [currency.code, currency]));

  const amountInput = document.getElementById("amount-input");
  const baseSelect = document.getElementById("base-select");
  const quoteSelect = document.getElementById("quote-select");
  const swapButton = document.getElementById("swap-button");
  const statusBanner = document.getElementById("status-banner");
  const baseFlag = document.getElementById("base-flag");
  const baseValue = document.getElementById("base-value");
  const quoteFlag = document.getElementById("quote-flag");
  const convertedValue = document.getElementById("converted-value");
  const rateValue = document.getElementById("rate-value");
  const lastUpdated = document.getElementById("last-updated");
  const nextUpdated = document.getElementById("next-updated");
  const providerName = document.getElementById("provider-name");
  const historyList = document.getElementById("history-list");
  const refreshHistoryButton = document.getElementById("refresh-history");
  const alertsForm = document.getElementById("alerts-form");
  const emailInput = document.getElementById("email-input");
  const alertsMessage = document.getElementById("alerts-message");

  let debounceTimer = null;
  let activeController = null;
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (!prefersReducedMotion) {
    const parallaxNodes = Array.from(document.querySelectorAll("[data-parallax-speed]"));
    let pointerX = window.innerWidth / 2;
    let pointerY = window.innerHeight / 2;
    let animationFrameId = 0;

    const updateParallax = () => {
      const viewportWidth = Math.max(window.innerWidth, 1);
      const viewportHeight = Math.max(window.innerHeight, 1);
      const offsetX = (pointerX - viewportWidth / 2) / viewportWidth;
      const offsetY = (pointerY - viewportHeight / 2) / viewportHeight;
      const scrollY = window.scrollY || window.pageYOffset;

      parallaxNodes.forEach((node) => {
        const speed = Number(node.dataset.parallaxSpeed || 0);
        const drift = Number(node.dataset.parallaxDrift || 0);
        const x = offsetX * drift;
        const y = scrollY * speed + offsetY * drift * 0.7;
        const rotate = offsetX * drift * 0.08;

        node.style.setProperty("--parallax-x", `${x.toFixed(2)}px`);
        node.style.setProperty("--parallax-y", `${y.toFixed(2)}px`);
        node.style.setProperty("--parallax-rotate", `${rotate.toFixed(2)}deg`);
      });

      animationFrameId = 0;
    };

    const queueParallax = () => {
      if (animationFrameId) {
        return;
      }
      animationFrameId = window.requestAnimationFrame(updateParallax);
    };

    window.addEventListener(
      "mousemove",
      (event) => {
        pointerX = event.clientX;
        pointerY = event.clientY;
        queueParallax();
      },
      { passive: true }
    );

    window.addEventListener(
      "scroll",
      () => {
        queueParallax();
      },
      { passive: true }
    );

    window.addEventListener(
      "resize",
      () => {
        pointerX = window.innerWidth / 2;
        pointerY = window.innerHeight / 2;
        queueParallax();
      },
      { passive: true }
    );

    queueParallax();
  }

  function normalizeAmount(value) {
    const trimmed = String(value || "").trim();
    if (!trimmed) {
      return null;
    }

    if (trimmed.includes(",") && trimmed.includes(".")) {
      if (trimmed.lastIndexOf(",") > trimmed.lastIndexOf(".")) {
        return trimmed.replace(/\./g, "").replace(",", ".");
      }
      return trimmed.replace(/,/g, "");
    }

    return trimmed.replace(",", ".");
  }

  function updatePairUrl() {
    const baseCurrency = baseSelect.value.toLowerCase();
    const quoteCurrency = quoteSelect.value.toLowerCase();
    if (baseCurrency === quoteCurrency) {
      window.history.replaceState({}, "", appState.endpoints.home);
      return;
    }
    const slug = `${baseCurrency}-${quoteCurrency}`;
    const nextUrl = `${appState.endpoints.pairPrefix}${slug}`;
    window.history.replaceState({}, "", nextUrl);
  }

  function setStatus(message, kind) {
    statusBanner.textContent = message;
    statusBanner.classList.remove("is-ok", "is-warning");
    statusBanner.classList.add(kind === "warning" ? "is-warning" : "is-ok");
  }

  function renderHistory(items) {
    if (!Array.isArray(items) || items.length === 0) {
      historyList.innerHTML = '<li class="empty-state">Todavia no hay conversiones guardadas.</li>';
      return;
    }

    historyList.innerHTML = items
      .map(
        (item) => `
          <li>
            <div class="history-main">
              <span class="history-side">
                <img src="${item.base_flag}" alt="" class="flag">
                ${item.amount_display} ${item.base_currency}
              </span>
              <span class="history-arrow">&rarr;</span>
              <span class="history-side accent">
                <img src="${item.quote_flag}" alt="" class="flag">
                ${item.converted_amount_display} ${item.quote_currency}
              </span>
            </div>
            <div class="history-meta">
              <span>${item.provider}</span>
              <span>${item.created_at}</span>
              ${item.stale ? '<span class="pill-warning">cacheada</span>' : ""}
            </div>
          </li>
        `
      )
      .join("");
  }

  async function refreshHistory() {
    try {
      const response = await fetch(`${appState.endpoints.history}?limite=${appState.historyLimit}`, {
        headers: { Accept: "application/json" },
      });
      const historyItems = await response.json();
      renderHistory(historyItems);
    } catch (error) {
      console.warn("No se pudo actualizar el historial", error);
    }
  }

  async function convert() {
    const normalizedAmount = normalizeAmount(amountInput.value);
    if (!normalizedAmount) {
      setStatus("Introduce una cantidad valida para calcular.", "warning");
      return;
    }

    if (activeController) {
      activeController.abort();
    }

    activeController = new AbortController();
    setStatus("Calculando conversion...", "ok");

    try {
      const response = await fetch(appState.endpoints.convert, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          cantidad: normalizedAmount,
          moneda_origen: baseSelect.value,
          moneda_destino: quoteSelect.value,
        }),
        signal: activeController.signal,
      });

      const payload = await response.json();
      if (!response.ok) {
        setStatus(payload.error || "No se pudo completar la conversion.", "warning");
        return;
      }

      const quoteCurrency = currencies[payload.quote_currency];
      const baseCurrency = currencies[payload.base_currency];
      baseFlag.src = baseCurrency.flag_url;
      baseValue.textContent = `${payload.amount_display} ${baseCurrency.code}`;
      quoteFlag.src = quoteCurrency.flag_url;
      convertedValue.textContent = `${payload.converted_amount_display} ${quoteCurrency.code}`;
      rateValue.textContent = payload.rate_display;
      lastUpdated.textContent = payload.last_updated || "Sin dato";
      nextUpdated.textContent = payload.next_update || "Sin dato";
      providerName.textContent = payload.provider;

      if (payload.stale) {
        setStatus("La fuente principal no respondio y se ha mostrado una tasa cacheada.", "warning");
      } else {
        setStatus(`Conversion lista para ${payload.base_currency}/${payload.quote_currency}.`, "ok");
      }

      updatePairUrl();
      await refreshHistory();
    } catch (error) {
      if (error.name === "AbortError") {
        return;
      }
      setStatus("Fallo de red. Revisa tu conexion e intentalo otra vez.", "warning");
    } finally {
      activeController = null;
    }
  }

  function scheduleConvert() {
    window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(convert, 280);
  }

  swapButton.addEventListener("click", () => {
    const previousBase = baseSelect.value;
    baseSelect.value = quoteSelect.value;
    quoteSelect.value = previousBase;
    scheduleConvert();
  });

  document.querySelectorAll("[data-amount]").forEach((button) => {
    button.addEventListener("click", () => {
      amountInput.value = button.dataset.amount;
      scheduleConvert();
    });
  });

  amountInput.addEventListener("input", scheduleConvert);
  baseSelect.addEventListener("change", scheduleConvert);
  quoteSelect.addEventListener("change", scheduleConvert);

  refreshHistoryButton.addEventListener("click", refreshHistory);

  alertsForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    alertsMessage.textContent = "";
    alertsMessage.className = "form-message";

    try {
      const response = await fetch(appState.endpoints.subscribe, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          email: emailInput.value,
          moneda_origen: baseSelect.value,
          moneda_destino: quoteSelect.value,
        }),
      });

      const payload = await response.json();
      if (!response.ok) {
        alertsMessage.textContent = payload.error || "No pudimos guardar tu interes.";
        alertsMessage.classList.add("is-error");
        return;
      }

      alertsMessage.textContent = payload.message;
      alertsMessage.classList.add("is-success");
      alertsForm.reset();
    } catch (error) {
      alertsMessage.textContent = "No pudimos conectar con el servidor para apuntarte a la beta.";
      alertsMessage.classList.add("is-error");
    }
  });

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/static/sw.js").catch(() => {});
    });
  }
}
