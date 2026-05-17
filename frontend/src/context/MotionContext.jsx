import { createContext, useContext, useEffect, useMemo, useState } from "react";

const MotionContext = createContext({
  allowPin: false,
  enableSmoothScroll: false,
  isMobile: false,
  motionScale: 0,
  parallaxScale: 0,
  prefersReducedMotion: false,
});

function readMatch(query) {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return false;
  }

  return window.matchMedia(query).matches;
}

export function MotionProvider({ children }) {
  const [isMobile, setIsMobile] = useState(() => readMatch("(max-width: 767px)"));
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() =>
    readMatch("(prefers-reduced-motion: reduce)")
  );

  useEffect(() => {
    const mobileMedia = window.matchMedia("(max-width: 767px)");
    const reducedMedia = window.matchMedia("(prefers-reduced-motion: reduce)");

    const handleMobile = (event) => {
      setIsMobile(event.matches);
    };

    const handleReduced = (event) => {
      setPrefersReducedMotion(event.matches);
    };

    mobileMedia.addEventListener("change", handleMobile);
    reducedMedia.addEventListener("change", handleReduced);

    return () => {
      mobileMedia.removeEventListener("change", handleMobile);
      reducedMedia.removeEventListener("change", handleReduced);
    };
  }, []);

  const value = useMemo(() => {
    const motionScale = prefersReducedMotion ? 0 : isMobile ? 0.45 : 1;
    const parallaxScale = prefersReducedMotion ? 0 : isMobile ? 0.38 : 1;

    return {
      allowPin: !prefersReducedMotion && !isMobile,
      enableSmoothScroll: !prefersReducedMotion && !isMobile,
      isMobile,
      motionScale,
      parallaxScale,
      prefersReducedMotion,
    };
  }, [isMobile, prefersReducedMotion]);

  return <MotionContext.Provider value={value}>{children}</MotionContext.Provider>;
}

export function useMotionSettings() {
  return useContext(MotionContext);
}
