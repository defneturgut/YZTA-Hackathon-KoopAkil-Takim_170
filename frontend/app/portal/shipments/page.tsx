"use client";

import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, MapPin, Truck } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { endpoints } from "@/lib/api";
import { formatRelative } from "@/lib/utils";

interface MyShipment {
  id: number;
  tracking_code: string;
  carrier: string;
  status: string;
  origin_city: string;
  destination_city: string;
  current_location: string;
  estimated_delivery: string | null;
  delivered_at: string | null;
  created_at: string;
  logs: {
    event: string;
    location: string | null;
    note: string | null;
    created_at: string;
  }[];
}

const STATUS_TR: Record<string, string> = {
  created: "Oluşturuldu",
  picked_up: "Teslim Alındı",
  in_transit: "Yolda",
  at_hub: "Aktarma Merkezinde",
  out_for_delivery: "Dağıtımda",
  delivered: "Teslim Edildi",
  delayed: "Gecikti",
  exception: "Sorunlu",
};

const STATUS_TONE: Record<
  string,
  "sage" | "info" | "warning" | "success" | "muted" | "danger"
> = {
  created: "muted",
  picked_up: "info",
  in_transit: "info",
  at_hub: "info",
  out_for_delivery: "sage",
  delivered: "success",
  delayed: "warning",
  exception: "danger",
};

export default function CustomerShipmentsPage() {
  const { data, isLoading } = useQuery<MyShipment[]>({
    queryKey: ["my-shipments"],
    queryFn: endpoints.myShipments,
  });

  const list = data ?? [];

  return (
    <Shell>
      <PageHeader
        title="Kargolarım 🚚"
        description="Aktif ve geçmiş kargolarınızı, teslimat hareketleriyle birlikte görüntüleyin."
      />

      <div className="space-y-4 p-6">
        {isLoading && <Card className="p-6 text-sm text-ink-500">Yükleniyor…</Card>}
        {list.length === 0 && !isLoading && (
          <Card className="p-10 text-center text-sm text-ink-500">
            Henüz kargo bulunamadı 🌿
          </Card>
        )}

        {list.map((s) => (
          <Card key={s.id}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Truck className="h-4 w-4 text-sage-600" />
                <span className="font-mono text-sm">{s.tracking_code}</span>
                <span className="text-sm font-normal text-ink-500">
                  · {s.carrier}
                </span>
              </CardTitle>
              <Badge tone={STATUS_TONE[s.status] ?? "muted"}>
                {STATUS_TR[s.status] ?? s.status}
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="mb-4 flex items-center gap-2 rounded-lg bg-cream-50 px-3 py-2 text-sm text-ink-600">
                <MapPin className="h-4 w-4 text-sage-600" />
                <span className="font-medium text-ink-700">
                  {s.origin_city}
                </span>
                <span className="text-ink-400">→</span>
                <span className="font-medium text-ink-700">
                  {s.destination_city}
                </span>
                <span className="ml-auto text-xs text-ink-500">
                  Son konum: {s.current_location}
                </span>
              </div>

              {/* ---- Timeline ----------------------------------- */}
              <ol className="relative space-y-3 border-l-2 border-cream-200 pl-5">
                {s.logs.map((log, idx) => {
                  const isLast = idx === s.logs.length - 1;
                  return (
                    <li key={`${log.event}-${idx}`} className="relative">
                      <span
                        className={
                          "absolute -left-[26px] grid h-4 w-4 place-items-center rounded-full border-2 " +
                          (isLast
                            ? "border-sage-500 bg-sage-500"
                            : "border-cream-300 bg-white")
                        }
                      >
                        {isLast && (
                          <CheckCircle2 className="h-3 w-3 text-white" />
                        )}
                      </span>
                      <div className="text-sm font-medium text-ink-700">
                        {log.event}
                      </div>
                      <div className="text-xs text-ink-500">
                        {log.location ? `${log.location} · ` : ""}
                        {formatRelative(log.created_at)}
                        {log.note ? ` · ${log.note}` : ""}
                      </div>
                    </li>
                  );
                })}
                {s.logs.length === 0 && (
                  <li className="text-xs text-ink-500">
                    Henüz hareket kaydı yok.
                  </li>
                )}
              </ol>
            </CardContent>
          </Card>
        ))}
      </div>
    </Shell>
  );
}
