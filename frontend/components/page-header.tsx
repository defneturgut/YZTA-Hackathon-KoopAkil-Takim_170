import { cn } from "@/lib/utils";

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function PageHeader({
  title,
  description,
  actions,
  className,
  ...props
}: Props) {
  return (
    <div
      className={cn(
        "flex flex-col gap-3 border-b border-cream-200 bg-white/60 px-6 py-6 md:flex-row md:items-center md:justify-between",
        className,
      )}
      {...props}
    >
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-ink-700">
          {title}
        </h1>
        {description ? (
          <p className="mt-1 max-w-2xl text-sm text-ink-500">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}
