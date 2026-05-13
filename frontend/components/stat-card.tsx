import * as React from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  hint?: string;
  icon?: React.ComponentType<{ className?: string }>;
  tone?: "default" | "success" | "warning" | "danger" | "earth";
}

const toneStyles: Record<NonNullable<Props["tone"]>, { ring: string; icon: string }> = {
  default: { ring: "before:bg-sage-300", icon: "bg-sage-50 text-sage-600" },
  success: { ring: "before:bg-sage-400", icon: "bg-sage-50 text-sage-600" },
  warning: { ring: "before:bg-warning", icon: "bg-warning/10 text-earth-500" },
  danger: { ring: "before:bg-danger", icon: "bg-danger/10 text-danger" },
  earth: { ring: "before:bg-earth-300", icon: "bg-earth-50 text-earth-500" },
};

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "default",
  className,
  ...props
}: Props) {
  const styles = toneStyles[tone];
  return (
    <Card
      className={cn(
        "relative overflow-hidden px-5 py-5 before:absolute before:left-0 before:top-0 before:h-full before:w-1.5 before:content-['']",
        styles.ring,
        className,
      )}
      {...props}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-400">
            {label}
          </div>
          <div className="mt-2 text-3xl font-bold tracking-tight text-ink-700">
            {value}
          </div>
          {hint ? (
            <div className="mt-1 text-xs text-ink-500">{hint}</div>
          ) : null}
        </div>
        {Icon ? (
          <div
            className={cn(
              "rounded-xl p-2.5",
              styles.icon,
            )}
          >
            <Icon className="h-5 w-5" />
          </div>
        ) : null}
      </div>
    </Card>
  );
}
