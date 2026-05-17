export function getBootstrapData() {
  const element = document.getElementById("bootstrap-data");
  if (!element?.textContent) {
    return {};
  }

  try {
    return JSON.parse(element.textContent);
  } catch (error) {
    console.warn("No se pudo leer el estado inicial de Flask.", error);
    return {};
  }
}
