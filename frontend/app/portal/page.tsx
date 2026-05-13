"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  Clock,
  Leaf,
  Package,
  Sparkles,
  Truck,
} from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { endpoints } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { formatCurrency, formatRelative } from "@/lib/utils";

interface MyOrder {
  id: number;
  order_code: string;
  status: string;
  total_amount: number;
  shipping_city: string;
  shipping_address: string;
  created_at: string;
  items_count: number;
  tracking_codes: string[];
}

const STATUS_TR: Record<string, string> = {
  pending: "Hazırlanıyor",
  preparing: "Hazırlanıyor",
  ready: "Kargoya Hazır",
  shipped: "Kargoda",
  delivered: "Teslim Edildi",
  cancelled: "İptal",
};

const STATUS_TONE: Record<
  string,
  "sage" | "info" | "warning" | "success" | "muted" | "danger"
> = {
  pending: "muted",
  preparing: "info",
  ready: "info",
  shipped: "sage",
  delivered: "success",
  cancelled: "danger",
};

export default function CustomerPortalPage() {
  const user = useAuthStore((s) => s.user);
  const { data: orders, isLoading } = useQuery<MyOrder[]>({
    queryKey: ["my-orders"],
    queryFn: endpoints.myOrders,
  });

  const list = orders ?? [];
  const active = list.filter((o) => !["delivered", "cancelled"].includes(o.status));
  const past = list.filter((o) => o.status === "delivered" || o.status === "cancelled");

  return (
    <Shell>
      <PageHeader
        title={`Merhaba, ${user?.full_name?.split(" ")[0] ?? ""} 🌿`}
        description="Siparişlerinizi ve kargolarınızı buradan takip edebilirsiniz."
      />

      <div className="space-y-6 p-6">
        <section className="grid gap-4 md:grid-cols-3">
          <Card className="p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-400">
              Aktif Siparişler
            </div>
            <div className="mt-2 flex items-center gap-2 text-3xl font-bold text-sage-700">
              {active.length}
              <Package className="h-6 w-6 text-sage-500" />
            </div>
          </Card>
          <Card className="p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-400">
              Geçmiş Siparişler
            </div>
            <div className="mt-2 flex items-center gap-2 text-3xl font-bold text-ink-700">
              {past.length}
              <CheckCircle2 className="h-6 w-6 text-ink-400" />
            </div>
          </Card>
          <Card className="p-5 bg-gradient-to-br from-sage-50 to-cream-50">
            <div className="text-xs font-semibold uppercase tracking-wider text-sage-700">
              Yardım mı lazım?
            </div>
            <div className="mt-2 text-sm text-ink-600">
              Kargonuz hakkında soru için takip kodu ile sorgulayabilirsiniz.
            </div>
            <Link href="/portal/shipments">
              <Button variant="subtle" size="sm" className="mt-3">
                <Truck className="h-4 w-4" />
                Kargoya Git
              </Button>
            </Link>
          </Card>
        </section>

        {/* ---- Aktif siparişler ----------------------------------- */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Leaf className="h-4 w-4 text-sage-600" />
              Aktif Siparişleriniz
            </CardTitle>
            <Badge tone="sage">{active.length} sipariş</Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            {isLoading && (
              <div className="text-sm text-ink-500">Yükleniyor…</div>
            )}
            {active.length === 0 && !isLoading && (
              <div className="rounded-xl border border-dashed border-cream-300 p-8 text-center text-sm text-ink-500">
                Şu an aktif siparişiniz yok. 🌿
              </div>
            )}
            {active.map((o) => (
              <OrderCard key={o.id} order={o} />
            ))}
          </CardContent>
        </Card>

        {/* ---- Geçmiş --------------------------------------------- */}
        {past.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-ink-500" />
                Geçmiş Siparişleriniz
              </CardTitle>
              <Badge tone="muted">{past.length} sipariş</Badge>
            </CardHeader>
            <CardContent className="space-y-2">
              {past.map((o) => (
                <OrderCard key={o.id} order={o} compact />
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </Shell>
  );
}

function OrderCard({
  order,
  compact = false,
}: {
  order: MyOrder;
  compact?: boolean;
}) {
  return (
    <div
      className={
        compact
          ? "flex items-center justify-between rounded-lg border border-cream-200 bg-white px-4 py-3"
          : "rounded-xl border border-cream-200 bg-cream-50 p-4"
      }
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm font-semibold text-ink-700">
            {order.order_code}
          </span>
          <Badge tone={STATUS_TONE[order.status] ?? "muted"}>
            {STATUS_TR[order.status] ?? order.status}
          </Badge>
        </div>
        <div className="mt-1 text-xs text-ink-500">
          {order.items_count} ürün · {order.shipping_city} ·{" "}
          {formatRelative(order.created_at)}
        </div>
        {order.tracking_codes.length > 0 && !compact && (
          <div className="mt-2 flex flex-wrap gap-1">
            {order.tracking_codes.map((tc) => (
              <Badge key={tc} tone="sage">
                <Sparkles className="h-3 w-3" />
                {tc}
              </Badge>
            ))}
          </div>
        )}
      </div>
      <div className="text-right">
        <div className="text-sm font-bold text-ink-700">
          {formatCurrency(order.total_amount)}
        </div>
      </div>
    </div>
  );
}
