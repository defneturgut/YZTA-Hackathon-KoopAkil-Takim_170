import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "flex h-10 w-full rounded-lg border border-cream-200 bg-white px-3 py-2 text-sm text-ink-700 placeholder:text-ink-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-300 focus-visible:border-sage-400 disabled:cursor-not-allowed disabled:opacity-60 transition-colors",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "flex min-h-[60px] w-full rounded-lg border border-cream-200 bg-white px-3 py-2 text-sm text-ink-700 placeholder:text-ink-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-300 focus-visible:border-sage-400 transition-colors",
      className,
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";
