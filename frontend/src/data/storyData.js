export function buildLandingData(bootstrap) {
  const pairLabel = bootstrap.selectedPair?.pairLabel ?? "Euro a Dolar estadounidense";
  const amountDisplay = bootstrap.liveSnapshot?.amountDisplay ?? "1.00";
  const convertedDisplay = bootstrap.liveSnapshot?.convertedAmountDisplay ?? "1.17";
  const baseCurrency = bootstrap.selectedPair?.baseCurrency ?? "EUR";
  const quoteCurrency = bootstrap.selectedPair?.quoteCurrency ?? "USD";
  const provider = bootstrap.liveSnapshot?.provider ?? "Fuente en vivo";
  const lastUpdated = bootstrap.liveSnapshot?.lastUpdated ?? "Actualizado ahora";
  const quickPairs = bootstrap.quickPairs ?? [];
  const historyItems = bootstrap.historyItems ?? [];

  return {
    pairLabel,
    heroStats: [
      { label: "Divisas activas", value: bootstrap.metrics?.currencies ?? 16 },
      { label: "Pares destacados", value: quickPairs.length || 8 },
      { label: "Historial visible", value: historyItems.length || 6 },
    ],
    heroLiveCard: {
      label: "Par del momento",
      title: pairLabel,
      body: `${amountDisplay} ${baseCurrency} -> ${convertedDisplay} ${quoteCurrency}`,
      meta: provider,
      updatedAt: lastUpdated,
    },
    signalSteps: [
      {
        id: "timing",
        headline: "No solo cambias divisas, cambias timing y margen.",
        copy:
          "Cada escena del scroll cuenta el valor del producto como si fuera una narrativa premium: contexto, lectura del movimiento y decision clara.",
        bullets: [
          { label: "Lectura", value: "Capas que guian la atencion" },
          { label: "Ritmo", value: "Scroll suave y progresivo" },
          { label: "Profundidad", value: "Movimiento por planos" },
          { label: "Sensacion", value: "SaaS premium sin ruido" },
        ],
      },
      {
        id: "focus",
        headline: "Las secciones se quedan contigo mientras revelan la historia.",
        copy:
          "Los bloques pinned dejan respirar el contenido. El usuario no recibe pantallas sueltas: siente una secuencia, una escena, un argumento visual.",
        bullets: [
          { label: "Pin", value: "Control del foco visual" },
          { label: "Fade", value: "Transiciones con calma" },
          { label: "Depth", value: "Capas lentas y legibles" },
          { label: "Polish", value: "Microinteracciones elegantes" },
        ],
      },
      {
        id: "trust",
        headline: "El movimiento ya vende claridad antes de que el usuario lea todo.",
        copy:
          "Cuando el scroll transmite seguridad, la propuesta se entiende como producto serio. Esa sensacion es clave para retencion, conversion y marca.",
        bullets: [
          { label: "Confianza", value: "Visuales con precision" },
          { label: "Marca", value: "Naranja editorial y limpio" },
          { label: "CTA", value: "Siempre visible sin forzar" },
          { label: "Mobile", value: "Menos movimiento, misma presencia" },
        ],
      },
    ],
    signalSlides: [
      {
        id: "signal-1",
        badge: "Escena 01",
        headline: "Capas lentas que construyen profundidad.",
        body:
          "Fondo, capa media, foreground y elementos flotantes se mueven con ritmos distintos para que el scroll se sienta cinematografico, no decorativo.",
        items: [
          { label: "Parallax base", value: "0.12x a 0.38x" },
          { label: "Foreground", value: "0.56x a 0.72x" },
          { label: "Legibilidad", value: "Siempre prioritaria" },
          { label: "Tono", value: "Editorial / premium" },
        ],
      },
      {
        id: "signal-2",
        badge: "Escena 02",
        headline: "Texto que entra como una escena, no como un popup.",
        body:
          "Los mensajes aparecen con fade y translateY suaves mientras el resto del escenario cambia por debajo. Todo acompasa el relato visual.",
        items: [
          { label: "Reveal", value: "Fade + blur + lift" },
          { label: "Scroll", value: "Scrub con GSAP" },
          { label: "Pins", value: "3 bloques inmersivos" },
          { label: "Metrica", value: "Menos jank, mas calma" },
        ],
      },
      {
        id: "signal-3",
        badge: "Escena 03",
        headline: "La experiencia parece producto desde el primer segundo.",
        body:
          "La landing no se siente como una web estandar. Se lee como una propuesta con intencion, detalle visual y un ritmo de narrativa mucho mas cuidado.",
        items: [
          { label: "Estilo", value: "Naranja + marfil" },
          { label: "Tipografia", value: "Grande y clara" },
          { label: "Espacio", value: "Aire para destacar" },
          { label: "Impacto", value: "Memorable y limpio" },
        ],
      },
    ],
    workflowSteps: [
      {
        id: "storytelling",
        headline: "Cada tarjeta entra como una pieza de producto viva.",
        copy:
          "La segunda escena pinned usa tarjetas escaladas, opacidad gradual y trayectorias suaves para reforzar la idea de stack premium.",
        bullets: [
          { label: "Scale", value: "0.92 a 1.00" },
          { label: "Opacity", value: "Entrada progresiva" },
          { label: "Offset", value: "Desplazamiento contenido" },
          { label: "Flow", value: "Secuencia sin cortes" },
        ],
      },
      {
        id: "system",
        headline: "El sistema visual es modular y facil de retocar.",
        copy:
          "ParallaxSection, LayeredScene y StickyStorySection dejan el motion desacoplado del contenido para iterar rapido sin reescribirlo todo.",
        bullets: [
          { label: "Props", value: "Velocidad y direccion" },
          { label: "Pin", value: "Duracion editable" },
          { label: "Layers", value: "Totalmente reutilizables" },
          { label: "GSAP", value: "Control fino por escena" },
        ],
      },
      {
        id: "launch",
        headline: "Listo para seguir creciendo como landing SaaS.",
        copy:
          "El resultado ya parece una base de marca y captacion, no solo una interfaz funcional. Eso deja margen para onboarding, pricing o comparadores premium.",
        bullets: [
          { label: "Base", value: "Escalable y limpia" },
          { label: "CTA", value: "Pensado para conversion" },
          { label: "Backend", value: "Flask sigue vivo" },
          { label: "Responsive", value: "Degrada con criterio" },
        ],
      },
    ],
    workflowSlides: [
      {
        id: "workflow-1",
        badge: "Bloque 01",
        headline: "Paneles de mercado con entrada progresiva.",
        body:
          "Las tarjetas no saltan: aparecen con una coreografia de escala, desplazamiento y opacidad para conservar serenidad y detalle.",
        items: [
          { label: "Animacion", value: "Scale + opacity" },
          { label: "Espacio", value: "Aire alrededor" },
          { label: "Lectura", value: "Jerarquia editorial" },
          { label: "Motion", value: "Preciso y silencioso" },
        ],
      },
      {
        id: "workflow-2",
        badge: "Bloque 02",
        headline: "Componentes pensados para editar velocidades sin dolor.",
        body:
          "Cada escena admite props de intensidad, direccion, triggers y duracion del pin, para ajustar la experiencia sin tocar toda la estructura.",
        items: [
          { label: "Parallax", value: "Por capa y por seccion" },
          { label: "Trigger", value: "Entrada y salida" },
          { label: "Mobile", value: "Menor intensidad" },
          { label: "Reduced", value: "Animacion opcional" },
        ],
      },
      {
        id: "workflow-3",
        badge: "Bloque 03",
        headline: "El cierre empuja al CTA con una sensacion de llegada.",
        body:
          "Despues del recorrido pinned, la escena final se siente como resolucion visual: clara, limpia y preparada para convertir.",
        items: [
          { label: "Cierre", value: "CTA dominante" },
          { label: "Profundidad", value: "Capas aun activas" },
          { label: "Ritmo", value: "Desacelera con elegancia" },
          { label: "Marca", value: "Premium y recordable" },
        ],
      },
    ],
  };
}
