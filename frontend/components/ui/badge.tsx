import * as React from "react";

import { cn } from "@/lib/utils";

type Tone = "default" | "info" | "success" | "warning" | "danger" | "muted" | "sage" | "earth";

const tones: Record<Tone, string> = {
  default: "bg-cream-100 text-ink-700 border-cream-300",
  info: "bg-info/10 text-info border-info/30",
  success: "bg-sage-100 text-sage-700 border-sage-300",
  warning: "bg-warning/15 text-earth-500 border-warning/40",
  danger: "bg-danger/10 text-danger border-danger/30",
  muted: "bg-cream-100 text-ink-500 border-cream-300",
  sage: "bg-sage-50 text-sage-700 border-sage-200",
  earth: "bg-earth-100 text-earth-500 border-earth-200",
};

export function Badge({
  tone = "default",
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        tones[tone],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
