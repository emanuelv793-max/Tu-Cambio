import { useRef } from "react";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";

import { useMotionSettings } from "../context/MotionContext";
import { cn } from "../lib/cn";

const toneClasses = {
  glow: "bg-white/18 text-white border-white/30 shadow-[0_20px_80px_rgba(255,255,255,0.16)] backdrop-blur-2xl",
  pearl:
    "bg-white/88 text-[#57280e] border-[#f4b183]/40 shadow-[0_24px_48px_rgba(249,115,22,0.14)] backdrop-blur-xl",
  outline:
    "bg-[#fff7ef]/74 text-[#7a3714] border-[#f59d62]/35 shadow-[0_18px_42px_rgba(249,115,22,0.12)] backdrop-blur-xl",
};

export default function FloatingMedia({
  eyebrow,
  title,
  value,
  body,
  tone = "pearl",
  className,
  floatDistance = 16,
  duration = 5.4,
  children,
}) {
  const ref = useRef(null);
  const { motionScale, prefersReducedMotion } = useMotionSettings();

  useGSAP(
    () => {
      if (prefersReducedMotion || !ref.current) {
        return undefined;
      }

      const tween = gsap.to(ref.current, {
        y: -floatDistance * motionScale,
        duration,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });

      return () => tween.kill();
    },
    { scope: ref, dependencies: [duration, floatDistance, motionScale, prefersReducedMotion] }
  );

  return (
    <div
      ref={ref}
      className={cn(
        "group rounded-[28px] border px-5 py-4 transition-transform duration-500 hover:-translate-y-1",
        toneClasses[tone],
        className
      )}
    >
      {eyebrow ? (
        <span className="mb-3 inline-flex items-center gap-2 text-[0.68rem] uppercase tracking-[0.34em] opacity-80">
          <span className="h-2 w-2 rounded-full bg-current opacity-75" />
          {eyebrow}
        </span>
      ) : null}

      {value ? (
        <div className="mb-2 text-sm font-medium uppercase tracking-[0.24em] opacity-70">{value}</div>
      ) : null}

      {title ? <h3 className="text-xl font-semibold tracking-[-0.03em]">{title}</h3> : null}
      {body ? <p className="mt-2 text-sm leading-6 opacity-80">{body}</p> : null}
      {children}
    </div>
  );
}
