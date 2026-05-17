import { cn } from "../lib/cn";

export default function LayeredScene({ className, layers = [], registerLayer }) {
  return (
    <div className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}>
      {layers.map((layer) => (
        <div
          key={layer.id}
          ref={registerLayer}
          data-speed={layer.speed}
          data-shift={layer.shift ?? 140}
          data-direction={layer.direction ?? 1}
          data-rotate-range={layer.rotateRange ?? 0}
          data-x-shift={layer.xShift ?? 0}
          className={cn("absolute will-change-transform", layer.className)}
        >
          {layer.content}
        </div>
      ))}
    </div>
  );
}
