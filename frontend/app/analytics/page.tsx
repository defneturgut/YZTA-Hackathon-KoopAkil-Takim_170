"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { PageHeader } from "@/components/page-header";
import { Shell } from "@/components/shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { endpoints } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

const COLORS = ["#6b9080", "#a4c3b2", "#d4b07a", "#a4886a", "#7a9eb1"];

export default function AnalyticsPage() {
  const sales = useQuery({
    queryKey: ["analytics", "sales"],
    queryFn: () => endpoints.salesAnalytics(14),
    retry: 1,
  });
  const inventory = useQuery({
    queryKey: ["analytics", "inventory"],
    queryFn: endpoints.inventoryAnalytics,
    retry: 1,
  });
  const shipping = useQuery({
    queryKey: ["analytics", "shipping"],
    queryFn: endpoints.shippingAnalytics,
    retry: 1,
  });

  const allLoading = sales.isLoading && inventory.isLoading && shipping.isLoading;
  const allError = sales.isError && inventory.isError && shipping.isError;
  const hasData =
    (sales.data?.total_orders ?? 0) > 0 ||
    (inventory.data?.items?.length ?? 0) > 0 ||
    (shipping.data?.shipments?.length ?? 0) > 0;

  const inventoryPie = (inventory.data?.items ?? [])
    .slice(0, 5)
    .map((p: { name: string; stock_qty: number }) => ({
      name: p.name.length > 22 ? p.name.slice(0, 22) + "…" : p.name,
      value: p.stock_qty,
    }));

  const shippingByStatus = (() => {
    const rows = (shipping.data?.shipments ?? []) as { status: string }[];
    const map = new Map<string, number>();
    for (const r of rows) map.set(r.status, (map.get(r.status) ?? 0) + 1);
    return Array.from(map.entries()).map(([status, count]) => ({
      status,
      count,
    }));
  })();

  return (
    <Shell>
      <PageHeader
        title="Analitik"
        description="Satış trendleri, stok dağılımı ve kargo durumu — AI ile zenginleştirilmiş raporlar."
      />

      {allLoading && (
        <div className="mx-6 mt-6 rounded-xl border border-cream-200 bg-cream-50 p-6 text-sm text-ink-500">
          Veriler yükleniyor…
        </div>
      )}

      {allError && (
        <div className="mx-6 mt-6 rounded-xl border border-danger/30 bg-danger/5 p-6 text-sm text-danger">
          ⚠️ Analitik verileri alınamadı. Backend çalışıyor mu kontrol edin
          (<code className="font-mono">docker compose ps</code>).
        </div>
      )}

      {!allLoading && !allError && !hasData && (
        <div className="mx-6 mt-6 rounded-xl border border-cream-200 bg-cream-50 p-6 text-sm text-ink-500">
          Henüz analiz üretilecek veri yok. Sistem ilk siparişleri ve kargoları
          işledikçe bu sayfa otomatik olarak dolacak. 🌿
        </div>
      )}

      <div className="grid gap-4 p-6 lg:grid-cols-2">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Satış Trendi (son 14 gün)</CardTitle>
            <div className="text-xs text-ink-500">
              Toplam ciro:{" "}
              <span className="font-semibold text-ink-700">
                {formatCurrency(sales.data?.total_revenue ?? 0)}
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-72 w-full">
              <ResponsiveContainer>
                <BarChart data={sales.data?.sales_trend ?? []}>
                  <CartesianGrid strokeDasharray="2 4" stroke="#e5e1d5" />
                  <XAxis
                    dataKey="date"
                    stroke="#8a8b7e"
                    fontSize={11}
                    tickFormatter={(d) => (d ?? "").slice(5)}
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
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="orders" fill="#6b9080" name="Sipariş" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="revenue" fill="#a4886a" name="Ciro" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>En Yüksek Stoklu 5 Ürün</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 w-full">
              <ResponsiveContainer>
                <PieChart>
                  <Tooltip
                    contentStyle={{
                      background: "#ffffff",
                      border: "1px solid #e5e1d5",
                      borderRadius: 10,
                      color: "#3a3a3a",
                      fontSize: 12,
                    }}
                  />
                  <Pie
                    data={inventoryPie}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={88}
                    label={(p: { name: string }) => p.name}
                    labelLine={false}
                  >
                    {inventoryPie.map((_: unknown, i: number) => (
                      <Cell key={`c-${i}`} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Kargo Durumu Dağılımı</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 w-full">
              <ResponsiveContainer>
                <BarChart data={shippingByStatus} layout="vertical">
                  <CartesianGrid strokeDasharray="2 4" stroke="#e5e1d5" />
                  <XAxis type="number" stroke="#8a8b7e" fontSize={11} />
                  <YAxis
                    type="category"
                    dataKey="status"
                    stroke="#8a8b7e"
                    fontSize={11}
                    width={120}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#ffffff",
                      border: "1px solid #e5e1d5",
                      borderRadius: 10,
                      color: "#3a3a3a",
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="count" fill="#6b9080" name="Kargo" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}
