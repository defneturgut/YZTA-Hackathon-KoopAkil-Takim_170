"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Boxes,
  CheckCircle2,
  ClipboardList,
  Leaf,
  MessageCircle,
  ShieldCheck,
  Sparkles,
  Truck,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageHeader } from "@/components/page-header";
import { Shell } from "@/components/shell";
import { StatCard } from "@/components/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { endpoints } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { formatCurrency, formatNumber } from "@/lib/utils";

/**
 * Dashboard her rol için farklı içerik gösterir.
 *
 *  • manager / admin → tam yönetici özeti (KPI + AI içgörü + satış grafiği)
 *  • warehouse       → "Bugün hazırlanacak paketler" + stok uyarıları (sade)
 *  • courier         → "Bugünkü teslimat rotası" + geciken kargolar (sade)
 *  • support         → AI Asistan kısayolu + bekleyen müşteri konuşmaları
 */
export default function DashboardPage() {
  const role = useAuthStore((s) => s.user?.role);

  if (role === "warehouse") return <WarehouseDashboard />;
  if (role === "courier") return <CourierDashboard />;
  if (role === "support") return <SupportDashboard />;
  return <ManagerDashboard />;
}

/* ===================================================================== */
/* MANAGER / ADMIN                                                        */
/* ===================================================================== */
function ManagerDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["daily-dashboard"],
    queryFn: endpoints.dailyDashboard,
  });

  return (
    <Shell>
      <PageHeader
        title="Operasyon Merkezi"
        description="Günün özetini, kritik uyarıları ve AI içgörülerini tek ekranda görün."
        actions={
          <Badge tone="sage">
            <Sparkles className="h-3 w-3" />
            AI tarafından özetlendi
          </Badge>
        }
      />

      <div className="space-y-6 p-6">
        <section className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
          <StatCard
            label="Aktif Kargolar"
            value={isLoading ? "…" : formatNumber(data?.kpis.active_shipments ?? 0)}
            hint={`${data?.kpis.delayed_shipments ?? 0} dikkat gerekiyor`}
            icon={Truck}
            tone={data?.kpis.delayed_shipments ? "warning" : "default"}
          />
          <StatCard
            label="Kritik Stok"
            value={isLoading ? "…" : formatNumber(data?.kpis.low_stock_products ?? 0)}
            hint="Sipariş zamanı"
            icon={Boxes}
            tone="warning"
          />
          <StatCard
            label="Açık Görev"
            value={isLoading ? "…" : formatNumber(data?.kpis.open_tasks ?? 0)}
            hint="Bugün için"
            icon={ClipboardList}
          />
          <StatCard
            label="AI Konuşma"
            value={isLoading ? "…" : formatNumber(data?.kpis.ai_conversations_today ?? 0)}
            hint="Son 24 saat"
            icon={MessageCircle}
            tone="earth"
          />
          <StatCard
            label="Operasyon Sağlığı"
            value={
              isLoading
                ? "…"
                : `${Math.round((1 - (data?.kpis.operational_risk_score ?? 0)) * 100)}%`
            }
            hint="AI değerlendirmesi"
            icon={ShieldCheck}
            tone={
              (data?.kpis.operational_risk_score ?? 0) > 0.5 ? "danger" : "success"
            }
          />
        </section>

        <section className="grid items-start gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2 flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-sage-600" />
                Yönetici Özeti
              </CardTitle>
              <Badge tone="sage">Otomatik üretildi</Badge>
            </CardHeader>
            <CardContent className="flex-1 space-y-4">
              <p className="text-sm leading-relaxed text-ink-600">
                {data?.executive_summary ?? "Yönetici özeti hazırlanıyor…"}
              </p>
              <div className="grid gap-2">
                {data?.top_risks?.map((risk: string) => (
                  <div
                    key={risk}
                    className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/5 px-3 py-2 text-sm text-ink-700"
                  >
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-earth-500" />
                    <span className="break-words">{risk}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Leaf className="h-4 w-4 text-sage-600" />
                Bugünün Aksiyonları
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1">
              <ul className="space-y-2 text-sm max-h-[420px] overflow-y-auto pr-1">
                {(data?.today_action_items ?? []).slice(0, 8).map(
                  (item: string, idx: number) => (
                    <li
                      key={`${item}-${idx}`}
                      className="flex items-start gap-3 rounded-lg border border-cream-200 bg-cream-50 px-3 py-2"
                    >
                      <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-sage-100 text-xs font-bold text-sage-700">
                        {idx + 1}
                      </span>
                      <span className="min-w-0 flex-1 break-words text-ink-700">
                        {item}
                      </span>
                    </li>
                  ),
                )}
                {!data && (
                  <li className="text-ink-400">Aksiyonlar hazırlanıyor…</li>
                )}
              </ul>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-sage-600" />
                Satış Trendi (son 14 gün)
              </CardTitle>
              <div className="text-xs text-ink-500">
                Toplam ciro:{" "}
                <span className="font-semibold text-ink-700">
                  {formatCurrency(data?.kpis.total_revenue ?? 0)}
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-64 w-full">
                <ResponsiveContainer>
                  <LineChart data={data?.sales_trend ?? []}>
                    <CartesianGrid strokeDasharray="2 4" stroke="#e5e1d5" />
                    <XAxis
                      dataKey="date"
                      stroke="#8a8b7e"
                      fontSize={11}
                      tickFormatter={(d) => d.slice(5)}
                    />
                    <YAxis stroke="#8a8b7e" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        background: "#ffffff",
                        border: "1px solid #e5e1d5",
                        borderRadius: 10,
                        color: "#3a3a3a",
                        fontSize: 12,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="orders"
                      stroke="#6b9080"
                      strokeWidth={2.5}
                      dot={{ r: 3, fill: "#6b9080" }}
                      name="Sipariş"
                    />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      stroke="#a4886a"
                      strokeWidth={2.5}
                      dot={{ r: 3, fill: "#a4886a" }}
                      name="Ciro (TL)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-sage-600" />
                AI İçgörüleri
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(data?.ai_insights ?? []).map(
                (insight: {
                  title: string;
                  summary: string;
                  severity: string;
                  confidence: number;
                }) => (
                  <div
                    key={insight.title}
                    className="rounded-xl border border-cream-200 bg-cream-50 p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-ink-700">
                        {insight.title}
                      </div>
                      <Badge
                        tone={
                          insight.severity === "high"
                            ? "danger"
                            : insight.severity === "medium"
                              ? "warning"
                              : "sage"
                        }
                      >
                        {insight.severity}
                      </Badge>
                    </div>
                    <p className="mt-1.5 text-xs leading-relaxed text-ink-600">
                      {insight.summary}
                    </p>
                    <div className="mt-2 text-[10px] uppercase tracking-wide text-ink-400">
                      Güven: {Math.round(insight.confidence * 100)}%
                    </div>
                  </div>
                ),
              )}
            </CardContent>
          </Card>
        </section>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Boxes className="h-4 w-4 text-earth-500" />
              Stok Uyarıları
            </CardTitle>
            <Badge tone="warning">
              {(data?.inventory_alerts ?? []).length} ürün
            </Badge>
          </CardHeader>
          <CardContent>
            {data?.inventory_alerts?.length ? (
              <ul className="grid gap-2 text-sm md:grid-cols-2">
                {data.inventory_alerts.map((alert: string) => (
                  <li
                    key={alert}
                    className="rounded-lg border border-warning/30 bg-warning/5 px-3 py-2 text-ink-700"
                  >
                    {alert}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-sm text-ink-500">
                Şu an kritik stok uyarısı yok. 🌿
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}

/* ===================================================================== */
/* WAREHOUSE                                                              */
/* ===================================================================== */
function WarehouseDashboard() {
  const { data: tasks } = useQuery<
    {
      id: number;
      title: string;
      priority: string;
      assignee_role: string;
      status: string;
    }[]
  >({
    queryKey: ["tasks"],
    queryFn: endpoints.listTasks,
  });
  const { data: lowStock } = useQuery<{ name: string; sku: string; stock_qty: number; unit: string }[]>({
    queryKey: ["inventory", true],
    queryFn: () => endpoints.listProducts(true),
  });

  const myTasks = (tasks ?? []).filter(
    (t) => t.assignee_role === "warehouse" && t.status !== "done",
  );

  return (
    <Shell>
      <PageHeader
        title="Günaydın 🌱"
        description="Bugün hazırlamanız gereken paketler ve dikkat etmeniz gereken ürünler."
      />
      <div className="space-y-6 p-6">
        <section className="grid gap-4 md:grid-cols-3">
          <StatCard
            label="Bugünkü Görevler"
            value={myTasks.length}
            hint="Sizin için"
            icon={ClipboardList}
            tone="success"
          />
          <StatCard
            label="Kritik Stok"
            value={lowStock?.length ?? 0}
            hint="Sipariş zamanı"
            icon={Boxes}
            tone="warning"
          />
          <StatCard
            label="Tamamlanan"
            value={(tasks ?? []).filter((t) => t.status === "done").length}
            hint="Bu hafta"
            icon={CheckCircle2}
          />
        </section>

        <Card>
          <CardHeader>
            <CardTitle>📦 Hazırlanacak Paketler</CardTitle>
            <Link href="/tasks">
              <Button variant="subtle" size="sm">
                Tümünü Gör
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {myTasks.length ? (
              myTasks.map((t) => (
                <div
                  key={t.id}
                  className="flex items-start justify-between rounded-xl border border-cream-200 bg-cream-50 p-4"
                >
                  <div className="flex-1">
                    <div className="font-semibold text-ink-700">{t.title}</div>
                    <div className="mt-1 text-xs text-ink-500">
                      Öncelik: {t.priority}
                    </div>
                  </div>
                  <Badge
                    tone={
                      t.priority === "critical" || t.priority === "high"
                        ? "warning"
                        : "sage"
                    }
                  >
                    {t.priority}
                  </Badge>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-cream-300 p-8 text-center text-sm text-ink-500">
                Şu an sizin için bekleyen görev yok 🌿
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>🌾 Stoğu Azalan Ürünler</CardTitle>
            <Link href="/inventory">
              <Button variant="subtle" size="sm">
                Envantere Git
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-2">
            {lowStock?.length ? (
              lowStock.map((p) => (
                <div
                  key={p.sku}
                  className="flex items-center justify-between rounded-lg border border-warning/30 bg-warning/5 px-4 py-3"
                >
                  <div>
                    <div className="font-semibold text-ink-700">{p.name}</div>
                    <div className="text-xs text-ink-500">{p.sku}</div>
                  </div>
                  <Badge tone="warning">
                    Kalan: {p.stock_qty} {p.unit}
                  </Badge>
                </div>
              ))
            ) : (
              <div className="text-sm text-ink-500">
                Tüm stoklar yeterli düzeyde 🌿
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}

/* ===================================================================== */
/* COURIER                                                                */
/* ===================================================================== */
function CourierDashboard() {
  const { data: shipments } = useQuery<
    { id: number; tracking_code: string; destination_city: string; status: string; risk_score: number }[]
  >({
    queryKey: ["shipments"],
    queryFn: endpoints.listShipments,
  });
  const active = (shipments ?? []).filter(
    (s) => !["delivered", "exception"].includes(s.status),
  );
  const delayed = (shipments ?? []).filter(
    (s) => s.status === "delayed" || s.status === "exception",
  );

  return (
    <Shell>
      <PageHeader
        title="Bugünkü Teslimatlar 🚚"
        description="Rotanızı, teslim edilecek paketleri ve dikkat gereken kargoları görün."
      />
      <div className="space-y-6 p-6">
        <section className="grid gap-4 md:grid-cols-3">
          <StatCard label="Aktif Kargo" value={active.length} icon={Truck} tone="success" />
          <StatCard
            label="Riskli Kargo"
            value={delayed.length}
            hint="Müşteri bilgilendirilmeli"
            icon={AlertTriangle}
            tone="warning"
          />
          <StatCard
            label="Bugün Teslim"
            value={
              (shipments ?? []).filter((s) => s.status === "out_for_delivery").length
            }
            icon={CheckCircle2}
            tone="default"
          />
        </section>

        <Card>
          <CardHeader>
            <CardTitle>📍 Bugünkü Rotanız</CardTitle>
            <Link href="/shipments">
              <Button variant="subtle" size="sm">
                Tüm Kargolar
              </Button>
            </Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {active.length ? (
              active.slice(0, 8).map((s, i) => (
                <div
                  key={s.id}
                  className="flex items-center gap-4 rounded-xl border border-cream-200 bg-cream-50 p-4"
                >
                  <span className="grid h-9 w-9 place-items-center rounded-full bg-sage-100 text-sm font-bold text-sage-700">
                    {i + 1}
                  </span>
                  <div className="flex-1">
                    <div className="font-semibold text-ink-700">
                      {s.destination_city}
                    </div>
                    <div className="text-xs text-ink-500 font-mono">
                      {s.tracking_code}
                    </div>
                  </div>
                  <Badge
                    tone={
                      s.status === "delayed" || s.status === "exception"
                        ? "warning"
                        : "sage"
                    }
                  >
                    {s.status}
                  </Badge>
                </div>
              ))
            ) : (
              <div className="rounded-xl border border-dashed border-cream-300 p-8 text-center text-sm text-ink-500">
                Bugün teslim edilecek aktif kargo yok 🌿
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}

/* ===================================================================== */
/* SUPPORT                                                                */
/* ===================================================================== */
function SupportDashboard() {
  return (
    <Shell>
      <PageHeader
        title="Merhaba 💬"
        description="Müşteri sorularına AI asistanınla birlikte yanıt verin."
      />
      <div className="space-y-6 p-6">
        <Card className="bg-gradient-to-br from-sage-50 to-cream-50">
          <CardContent className="p-8 text-center">
            <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-white shadow-soft">
              <MessageCircle className="h-8 w-8 text-sage-600" />
            </div>
            <h2 className="mt-4 text-2xl font-bold text-ink-700">
              AI Müşteri Asistanı
            </h2>
            <p className="mx-auto mt-2 max-w-md text-sm text-ink-500">
              Müşteri soruları için AI asistanını açın. Sipariş takibi, iade
              süreci, ürün bilgisi gibi konularda anında yanıt üretir.
            </p>
            <Link href="/chat">
              <Button size="lg" className="mt-6">
                <MessageCircle className="h-4 w-4" />
                AI Asistanı Başlat
              </Button>
            </Link>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>📚 Bilgi Tabanı</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-ink-500">
                SSS, kargo politikası ve iade süreçleri AI asistanın bilgi
                tabanına yüklendi. Yeni belge eklemek için Ayarlar sayfasına
                gidin.
              </p>
              <Link href="/settings">
                <Button variant="subtle" size="sm" className="mt-3">
                  Belge Yönetimi
                </Button>
              </Link>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>🚚 Kargo Takibi</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-ink-500">
                Müşteri kargo sorduğunda doğrudan takip kodundan sorgulama
                yapabilirsiniz.
              </p>
              <Link href="/shipments">
                <Button variant="subtle" size="sm" className="mt-3">
                  Kargo Listesi
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </Shell>
  );
}
