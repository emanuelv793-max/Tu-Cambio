import { useRef } from "react";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";

import { useMotionSettings } from "../context/MotionContext";
import { cn } from "../lib/cn";

export default function RevealText({
  as: Component = "div",
  children,
  className,
  delay = 0,
  duration = 1.1,
  y = 36,
}) {
  const ref = useRef(null);
  const { prefersReducedMotion } = useMotionSettings();

  useGSAP(
    () => {
      if (prefersReducedMotion) {
        return undefined;
      }

      return gsap.fromTo(
        ref.current,
        { autoAlpha: 0, y, filter: "blur(12px)" },
        {
          autoAlpha: 1,
          y: 0,
          filter: "blur(0px)",
          delay,
          duration,
          ease: "power3.out",
          scrollTrigger: {
            trigger: ref.current,
            start: "top 84%",
            once: true,
          },
        }
      );
    },
    { scope: ref, dependencies: [delay, duration, prefersReducedMotion, y] }
  );

  return (
    <Component ref={ref} className={cn("will-change-transform", className)}>
      {children}
    </Component>
  );
}
