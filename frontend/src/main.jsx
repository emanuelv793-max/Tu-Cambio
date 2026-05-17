import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import { MotionProvider } from "./context/MotionContext";
import { getBootstrapData } from "./lib/getBootstrapData";
import "./index.css";

const bootstrap = getBootstrapData();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <MotionProvider>
      <App bootstrap={bootstrap} />
    </MotionProvider>
  </React.StrictMode>
);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch(() => {});
  });
}
