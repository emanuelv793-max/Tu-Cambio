import { useRef } from "react";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import { useMotionSettings } from "../context/MotionContext";
import { cn } from "../lib/cn";
import LayeredScene from "./LayeredScene";
import RevealText from "./RevealText";

function MediaSlide({ slide, className }) {
  return (
    <article
      className={cn(
        "absolute inset-0 rounded-[30px] border border-[#f4b183]/30 bg-white/85 p-6 shadow-[0_28px_60px_rgba(249,115,22,0.14)] backdrop-blur-xl",
        className
      )}
    >
      <div className="flex h-full flex-col justify-between gap-8">
        <div>
          <span className="inline-flex items-center gap-2 text-[0.68rem] font-semibold uppercase tracking-[0.34em] text-[#c65b12]">
            <span className="h-2 w-2 rounded-full bg-current" />
            {slide.badge}
          </span>
          <h3 className="mt-4 text-[clamp(1.6rem,2.4vw,2.3rem)] font-semibold leading-tight tracking-[-0.04em] text-[#381604]">
            {slide.headline}
          </h3>
          <p className="mt-4 max-w-[32rem] text-sm leading-7 text-[#8f522f]">{slide.body}</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {slide.items.map((item) => (
            <div key={item.label} className="rounded-[22px] border border-[#fed7aa]/70 bg-[#fff8f1] p-4">
              <div className="text-[0.68rem] uppercase tracking-[0.24em] text-[#c65b12]">{item.label}</div>
              <div className="mt-2 text-xl font-semibold tracking-[-0.03em] text-[#381604]">{item.value}</div>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}

export default function StickyStorySection({
  id,
  eyebrow,
  title,
  description,
  steps,
  mediaSlides,
  layers = [],
  pinDuration = "+=220%",
  className,
  intensity = 1,
}) {
  const sectionRef = useRef(null);
  const layerRefs = useRef([]);
  const stepRefs = useRef([]);
  const mediaRefs = useRef([]);
  const { allowPin, motionScale, parallaxScale, prefersReducedMotion } = useMotionSettings();

  layerRefs.current = [];
  stepRefs.current = [];
  mediaRefs.current = [];

  const registerLayer = (element) => {
    if (element && !layerRefs.current.includes(element)) {
      layerRefs.current.push(element);
    }
  };

  const registerStep = (element) => {
    if (element && !stepRefs.current.includes(element)) {
      stepRefs.current.push(element);
    }
  };

  const registerMedia = (element) => {
    if (element && !mediaRefs.current.includes(element)) {
      mediaRefs.current.push(element);
    }
  };

  useGSAP(
    () => {
      if (!allowPin || prefersReducedMotion) {
        return undefined;
      }

      const ctx = gsap.context(() => {
        layerRefs.current.forEach((layer) => {
          // Cada capa acepta velocidad distinta para crear profundidad sin exagerar la lectura.
          const speed = Number(layer.dataset.speed || 0.18) * parallaxScale;
          const shift = Number(layer.dataset.shift || 120) * motionScale;
          const direction = Number(layer.dataset.direction || 1);
          const rotateRange = Number(layer.dataset.rotateRange || 0) * motionScale;

          gsap.to(layer, {
            y: speed * shift * direction,
            rotation: speed * rotateRange * direction,
            ease: "none",
            scrollTrigger: {
              trigger: sectionRef.current,
              start: "top top",
              end: pinDuration,
              scrub: true,
            },
          });
        });

        gsap.set(stepRefs.current, { autoAlpha: 0, y: 34 * intensity });
        gsap.set(mediaRefs.current, { autoAlpha: 0, y: 38 * intensity, scale: 0.94 });

        const timeline = gsap.timeline({
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top top",
            end: pinDuration,
            scrub: true,
            pin: true,
            anticipatePin: 1,
          },
        });

        stepRefs.current.forEach((step, index) => {
          const media = mediaRefs.current[index];
          const label = `scene-${index}`;

          timeline.to(
            step,
            {
              autoAlpha: 1,
              y: 0,
              duration: 0.38,
              ease: "power2.out",
            },
            label
          );

          if (media) {
            timeline.to(
              media,
              {
                autoAlpha: 1,
                y: 0,
                scale: 1,
                duration: 0.42,
                ease: "power2.out",
              },
              `${label}+=0.04`
            );
          }

          if (index > 0) {
            timeline.to(
              stepRefs.current[index - 1],
              {
                autoAlpha: 0,
                y: -30 * intensity,
                duration: 0.28,
                ease: "power2.inOut",
              },
              `${label}-=0.05`
            );

            if (mediaRefs.current[index - 1]) {
              timeline.to(
                mediaRefs.current[index - 1],
                {
                  autoAlpha: 0,
                  y: -20 * intensity,
                  scale: 0.98,
                  duration: 0.3,
                  ease: "power2.inOut",
                },
                `${label}-=0.02`
              );
            }
          }
        });
      }, sectionRef);

      return () => ctx.revert();
    },
    {
      scope: sectionRef,
      dependencies: [allowPin, intensity, motionScale, parallaxScale, pinDuration, prefersReducedMotion],
    }
  );

  if (!allowPin) {
    return (
      <section id={id} className={cn("relative overflow-clip py-20", className)}>
        <LayeredScene className="absolute inset-0" layers={layers} registerLayer={registerLayer} />
        <div className="relative z-20 mx-auto grid w-full max-w-[1280px] gap-8 px-6 md:px-10">
          <div className="max-w-3xl">
            <RevealText className="inline-flex items-center gap-3 text-[0.75rem] font-semibold uppercase tracking-[0.34em] text-[#c65b12]">
              <span className="h-2 w-2 rounded-full bg-[#f97316]" />
              {eyebrow}
            </RevealText>
            <RevealText as="h2" className="mt-4 text-[clamp(2.4rem,7vw,4.4rem)] font-semibold leading-[0.95] tracking-[-0.05em] text-[#351303]">
              {title}
            </RevealText>
            <RevealText as="p" className="mt-4 max-w-2xl text-base leading-8 text-[#8f522f]">
              {description}
            </RevealText>
          </div>

          <div className="grid gap-5">
            {steps.map((step, index) => (
              <article
                key={step.id}
                className="rounded-[30px] border border-[#f4b183]/30 bg-white/88 p-6 shadow-[0_24px_48px_rgba(249,115,22,0.12)]"
              >
                <div className="text-[0.72rem] font-semibold uppercase tracking-[0.34em] text-[#c65b12]">
                  0{index + 1} / {steps.length}
                </div>
                <h3 className="mt-4 text-2xl font-semibold tracking-[-0.04em] text-[#351303]">{step.headline}</h3>
                <p className="mt-3 text-sm leading-7 text-[#8f522f]">{step.copy}</p>
                <ul className="mt-4 grid gap-3 sm:grid-cols-2">
                  {step.bullets.map((bullet) => (
                    <li key={bullet.label} className="rounded-[20px] bg-[#fff5eb] p-4">
                      <div className="text-[0.68rem] uppercase tracking-[0.24em] text-[#c65b12]">{bullet.label}</div>
                      <div className="mt-2 text-lg font-semibold text-[#381604]">{bullet.value}</div>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>

          <div className="grid gap-4">
            {mediaSlides.map((slide) => (
              <div key={slide.id} className="relative min-h-[28rem]">
                <MediaSlide slide={slide} />
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  return (
    <section id={id} ref={sectionRef} className={cn("relative min-h-screen overflow-clip", className)}>
      <LayeredScene className="absolute inset-0" layers={layers} registerLayer={registerLayer} />
      <div className="relative z-20 mx-auto flex min-h-screen w-full max-w-[1280px] items-center px-6 py-20 md:px-10">
        <div className="grid w-full items-center gap-12 lg:grid-cols-[minmax(0,0.88fr)_minmax(340px,0.98fr)]">
          <div>
            <RevealText className="inline-flex items-center gap-3 text-[0.75rem] font-semibold uppercase tracking-[0.34em] text-[#c65b12]">
              <span className="h-2 w-2 rounded-full bg-[#f97316]" />
              {eyebrow}
            </RevealText>
            <RevealText as="h2" className="mt-4 text-[clamp(2.8rem,6vw,4.6rem)] font-semibold leading-[0.95] tracking-[-0.05em] text-[#351303]">
              {title}
            </RevealText>
            <RevealText as="p" className="mt-4 max-w-2xl text-base leading-8 text-[#8f522f]">
              {description}
            </RevealText>

            <div className="relative mt-10 min-h-[24rem]">
              {steps.map((step, index) => (
                <article
                  key={step.id}
                  ref={registerStep}
                  className={cn(
                    "absolute inset-0 rounded-[30px] border border-[#f4b183]/24 bg-white/76 p-7 opacity-0 shadow-[0_24px_52px_rgba(249,115,22,0.1)] backdrop-blur-xl",
                    index === 0 ? "opacity-100" : ""
                  )}
                >
                  <div className="text-[0.72rem] font-semibold uppercase tracking-[0.34em] text-[#c65b12]">
                    0{index + 1} / {steps.length}
                  </div>
                  <h3 className="mt-4 text-[clamp(1.8rem,3vw,2.8rem)] font-semibold leading-tight tracking-[-0.04em] text-[#381604]">
                    {step.headline}
                  </h3>
                  <p className="mt-4 max-w-xl text-sm leading-7 text-[#8f522f]">{step.copy}</p>

                  <ul className="mt-8 grid gap-3 sm:grid-cols-2">
                    {step.bullets.map((bullet) => (
                      <li key={bullet.label} className="rounded-[22px] border border-[#fed7aa]/70 bg-[#fff7f0] p-4">
                        <div className="text-[0.68rem] uppercase tracking-[0.24em] text-[#c65b12]">{bullet.label}</div>
                        <div className="mt-2 text-lg font-semibold tracking-[-0.03em] text-[#381604]">{bullet.value}</div>
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>

          <div className="relative h-[38rem]">
            <div className="absolute inset-0 rounded-[38px] border border-[#f3bb92]/40 bg-[#fff6ef]/70 shadow-[0_28px_72px_rgba(249,115,22,0.12)] backdrop-blur-xl" />
            <div className="absolute inset-x-[10%] top-[12%] h-44 rounded-full bg-[#ffdfc4] blur-3xl opacity-70" />

            {mediaSlides.map((slide, index) => (
              <div
                key={slide.id}
                ref={registerMedia}
                className={cn("absolute inset-0 opacity-0", slide.positionClassName ?? "", index === 0 ? "opacity-100" : "")}
              >
                <MediaSlide slide={slide} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
