import { useRef } from "react";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import { useMotionSettings } from "../context/MotionContext";
import { cn } from "../lib/cn";
import LayeredScene from "./LayeredScene";

export default function ParallaxSection({
  id,
  pin = false,
  pinDuration = "+=160%",
  layers = [],
  className,
  contentClassName,
  sceneClassName,
  children,
}) {
  const sectionRef = useRef(null);
  const contentRef = useRef(null);
  const layerRefs = useRef([]);
  const { allowPin, motionScale, parallaxScale, prefersReducedMotion } = useMotionSettings();

  layerRefs.current = [];

  const registerLayer = (element) => {
    if (element && !layerRefs.current.includes(element)) {
      layerRefs.current.push(element);
    }
  };

  useGSAP(
    () => {
      if (prefersReducedMotion) {
        return undefined;
      }

      const enablePin = pin && allowPin;
      const endValue = enablePin ? pinDuration : "bottom top";

      const ctx = gsap.context(() => {
        if (enablePin) {
          ScrollTrigger.create({
            trigger: sectionRef.current,
            start: "top top",
            end: pinDuration,
            scrub: true,
            pin: true,
            anticipatePin: 1,
          });
        }

        layerRefs.current.forEach((layer) => {
          // Ajusta `speed` y `shift` en cada capa para subir o bajar la intensidad del parallax.
          const speed = Number(layer.dataset.speed || 0.2) * parallaxScale;
          const shift = Number(layer.dataset.shift || 140) * motionScale;
          const direction = Number(layer.dataset.direction || 1);
          const rotateRange = Number(layer.dataset.rotateRange || 0) * motionScale;
          const xShift = Number(layer.dataset.xShift || 0) * motionScale;

          gsap.to(layer, {
            y: speed * shift * direction,
            x: speed * xShift * direction,
            rotation: speed * rotateRange * direction,
            ease: "none",
            scrollTrigger: {
              trigger: sectionRef.current,
              start: "top bottom",
              end: enablePin ? pinDuration : endValue,
              scrub: true,
            },
          });
        });

        if (contentRef.current) {
          gsap.fromTo(
            contentRef.current,
            { y: 34 * motionScale, autoAlpha: 0.9, scale: 0.98 },
            {
              y: -20 * motionScale,
              autoAlpha: 1,
              scale: 1,
              ease: "none",
              scrollTrigger: {
                trigger: sectionRef.current,
                start: "top bottom",
                end: enablePin ? pinDuration : endValue,
                scrub: true,
              },
            }
          );
        }
      }, sectionRef);

      return () => ctx.revert();
    },
    {
      scope: sectionRef,
      dependencies: [allowPin, motionScale, parallaxScale, pin, pinDuration, prefersReducedMotion],
    }
  );

  return (
    <section id={id} ref={sectionRef} className={cn("relative min-h-screen overflow-clip", className)}>
      <LayeredScene className={sceneClassName} layers={layers} registerLayer={registerLayer} />
      <div
        ref={contentRef}
        className={cn(
          "relative z-20 mx-auto flex min-h-screen w-full max-w-[1280px] flex-col justify-center px-6 py-20 md:px-10",
          contentClassName
        )}
      >
        {children}
      </div>
    </section>
  );
}
