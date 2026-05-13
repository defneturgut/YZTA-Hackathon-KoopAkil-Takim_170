"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  BarChart3,
  Boxes,
  ClipboardList,
  Home,
  Leaf,
  LogOut,
  MessageCircle,
  Settings,
  Sparkles,
  Truck,
  User,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { endpoints } from "@/lib/api";
import { NAV_ROUTES, ROLE_LABEL, type AppRole } from "@/lib/roles";
import { useAuthStore } from "@/lib/store";
import { cn, initials } from "@/lib/utils";

const ICONS = {
  home: Home,
  chat: MessageCircle,
  boxes: Boxes,
  truck: Truck,
  tasks: ClipboardList,
  alert: AlertCircle,
  chart: BarChart3,
  settings: Settings,
  user: User,
} as const;

/**
 * Authenticated app chrome — beyaz/sage tasarım, rol bazlı sidebar.
 *
 * Kullanıcının rolü `NAV_ROUTES.allowedRoles` listesinde olmayan sayfalar
 * sidebar'da gösterilmez. Bu sayede depo görevlisi, kurye veya destek
 * kullanıcısı kafa karıştırıcı yönetim ekranlarıyla karşılaşmaz.
 */
export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.accessToken);
  const logout = useAuthStore((s) => s.logout);

  useEffect(() => {
    if (!token) router.replace("/login");
  }, [token, router]);

  const role = (user?.role as AppRole) ?? "manager";
  const visibleRoutes = useMemo(
    () => NAV_ROUTES.filter((r) => r.allowedRoles.includes(role)),
    [role],
  );

  return (
    <div className="flex min-h-screen bg-cream-50 text-ink-700">
      {/* ---- Sidebar ------------------------------------------------------ */}
      <aside className="hidden w-72 flex-col border-r border-cream-200 bg-white md:flex">
        <div className="flex items-center gap-3 px-6 py-6">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-sage-100 text-sage-600">
            <Leaf className="h-6 w-6" />
          </div>
          <div>
            <div className="text-lg font-bold tracking-tight text-ink-700">
              KoopAkıl
            </div>
            <div className="text-xs text-ink-500">
              Kooperatifinizin akıllı yardımcısı
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3">
          {visibleRoutes.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            const Icon = ICONS[item.iconKey];
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors",
                  active
                    ? "bg-sage-50 text-sage-700 font-semibold"
                    : "text-ink-600 hover:bg-cream-100 hover:text-ink-700",
                )}
              >
                <span
                  className={cn(
                    "grid h-9 w-9 place-items-center rounded-lg transition-colors",
                    active
                      ? "bg-sage-100 text-sage-700"
                      : "bg-cream-50 text-ink-500 group-hover:bg-cream-200",
                  )}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <span className="flex-1">
                  <div>{item.label}</div>
                  <div className="text-[11px] font-normal text-ink-400">
                    {item.description}
                  </div>
                </span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-cream-200 p-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-full bg-sage-100 text-sm font-semibold text-sage-700">
              {user ? initials(user.full_name) : "KA"}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-ink-700">
                {user?.full_name ?? "Misafir"}
              </div>
              <div className="truncate text-xs text-ink-500">
                {ROLE_LABEL[user?.role ?? ""] ?? "—"}
              </div>
            </div>
            <Button
              size="icon"
              variant="ghost"
              title="Çıkış"
              onClick={() => {
                logout();
                router.replace("/login");
              }}
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* ---- Main pane --------------------------------------------------- */}
      <main className="flex-1 bg-leaf-fade">
        <div className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-cream-200 bg-white/85 px-6 backdrop-blur-md">
          <div className="flex items-center gap-3 text-sm text-ink-500">
            <span className="grid h-2 w-2 place-items-center rounded-full bg-sage-500" />
            <span>Sistem çalışıyor</span>
          </div>
          <div className="flex items-center gap-2">
            <AIStatusBadge />
            <Badge tone="sage">
              {ROLE_LABEL[user?.role ?? ""] ?? "Hoş geldiniz"}
            </Badge>
            <Badge tone="muted">v1.0</Badge>
          </div>
        </div>
        {children}
      </main>
    </div>
  );
}

/* ---------------------------------------------------------------- */
/** Topbar'da AI durumu rozeti: Gemini bağlı mı yoksa mock'ta mı.  */
function AIStatusBadge() {
  const { data } = useQuery<{
    backend: string;
    ok: boolean;
    last_error?: string | null;
    key_looks_valid?: boolean;
  }>({
    queryKey: ["ai-health"],
    queryFn: endpoints.aiHealth,
    refetchInterval: 30_000,
    staleTime: 25_000,
  });

  if (!data) {
    return (
      <Badge tone="muted">
        <Sparkles className="h-3 w-3" />
        AI: bağlanıyor…
      </Badge>
    );
  }

  if (data.backend === "gemini" && data.ok) {
    return (
      <Badge tone="success" title="Gerçek Gemini 2.5 Pro'ya bağlı">
        <Sparkles className="h-3 w-3" />
        Gemini bağlı
      </Badge>
    );
  }

  return (
    <Badge
      tone="warning"
      title={
        data.key_looks_valid
          ? data.last_error ?? "Gemini cevap vermedi — mock fallback aktif"
          : "GEMINI_API_KEY eksik veya geçersiz — kök .env dosyasını kontrol edin"
      }
    >
      <Sparkles className="h-3 w-3" />
      AI: Mock modda
    </Badge>
  );
}
