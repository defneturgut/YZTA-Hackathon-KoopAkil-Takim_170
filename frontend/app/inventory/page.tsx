"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Minus, Plus, Sparkles } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TBody, TD, TH, THead, TR, Table } from "@/components/ui/table";
import { endpoints } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/utils";

interface Product {
  id: number;
  sku: string;
  name: string;
  category: string;
  unit: string;
  stock_qty: number;
  reorder_threshold: number;
  price: number;
  supplier_name: string | null;
  is_low_stock: boolean;
}

export default function InventoryPage() {
  const qc = useQueryClient();
  const [onlyLow, setOnlyLow] = useState(false);
  const [forecast, setForecast] = useState<{
    productId: number;
    text: string;
    structured: Record<string, unknown> | null;
    confidence: number;
  } | null>(null);

  const productsQ = useQuery<Product[]>({
    queryKey: ["inventory", onlyLow],
    queryFn: () => endpoints.listProducts(onlyLow),
  });

  const adjustMutation = useMutation({
    mutationFn: (vars: { id: number; qty: number; type: "inbound" | "outbound" }) =>
      endpoints.adjustInventory(vars.id, vars.qty, vars.type),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["inventory"] }),
  });

  const forecastMutation = useMutation({
    mutationFn: (id: number) => endpoints.forecastInventory(id),
    onSuccess: (data, id) =>
      setForecast({
        productId: id,
        text: data.ai_text,
        structured: data.forecast,
        confidence: data.confidence,
      }),
  });

  const products = productsQ.data ?? [];
  const criticalCount = products.filter((p) => p.is_low_stock).length;

  return (
    <Shell>
      <PageHeader
        title="Envanter"
        description="Ürün stoklarınızı takip edin, AI ile tükenme tahmini ve tedarikçi önerisi alın."
        actions={
          <Button
            variant={onlyLow ? "default" : "outline"}
            size="sm"
            onClick={() => setOnlyLow((v) => !v)}
          >
            <AlertTriangle className="h-4 w-4" />
            {onlyLow ? "Tümünü Göster" : "Sadece Kritik Stok"}
          </Button>
        }
      />

      <div className="space-y-6 p-6">
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-400">
              Toplam Ürün
            </div>
            <div className="mt-2 text-3xl font-bold text-ink-700">
              {formatNumber(products.length)}
            </div>
          </Card>
          <Card className="p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-400">
              Kritik Stok
            </div>
            <div className="mt-2 flex items-center gap-2 text-3xl font-bold text-earth-500">
              {formatNumber(criticalCount)}
              <Badge tone="warning">
                {Math.round((criticalCount / Math.max(1, products.length)) * 100)}%
              </Badge>
            </div>
          </Card>
          <Card className="p-5">
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-400">
              Toplam Stok Değeri
            </div>
            <div className="mt-2 text-3xl font-bold text-ink-700">
              {formatCurrency(
                products.reduce((sum, p) => sum + p.stock_qty * p.price, 0),
              )}
            </div>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Ürünleriniz</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <THead>
                <TR>
                  <TH>SKU</TH>
                  <TH>Ürün</TH>
                  <TH>Stok</TH>
                  <TH>Eşik</TH>
                  <TH>Fiyat</TH>
                  <TH>Tedarikçi</TH>
                  <TH className="text-right">İşlemler</TH>
                </TR>
              </THead>
              <TBody>
                {products.map((p) => (
                  <TR key={p.id}>
                    <TD className="font-mono text-xs text-ink-500">{p.sku}</TD>
                    <TD>
                      <div className="font-semibold text-ink-700">{p.name}</div>
                      <div className="text-xs text-ink-500">{p.category}</div>
                    </TD>
                    <TD>
                      <span
                        className={
                          p.is_low_stock
                            ? "font-bold text-earth-500"
                            : "font-semibold text-ink-700"
                        }
                      >
                        {formatNumber(p.stock_qty)} {p.unit}
                      </span>
                      {p.is_low_stock && (
                        <Badge tone="warning" className="ml-2">
                          azaldı
                        </Badge>
                      )}
                    </TD>
                    <TD className="text-ink-500">
                      {formatNumber(p.reorder_threshold)} {p.unit}
                    </TD>
                    <TD className="font-medium">{formatCurrency(p.price)}</TD>
                    <TD className="text-ink-500">{p.supplier_name ?? "—"}</TD>
                    <TD>
                      <div className="flex justify-end gap-1">
                        <Button
                          size="sm"
                          variant="subtle"
                          onClick={() =>
                            adjustMutation.mutate({ id: p.id, qty: 10, type: "inbound" })
                          }
                          title="Stok ekle (+10)"
                        >
                          <Plus className="h-3.5 w-3.5" /> 10
                        </Button>
                        <Button
                          size="sm"
                          variant="subtle"
                          onClick={() =>
                            adjustMutation.mutate({ id: p.id, qty: 1, type: "outbound" })
                          }
                          title="Stoktan çıkar (-1)"
                        >
                          <Minus className="h-3.5 w-3.5" /> 1
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => forecastMutation.mutate(p.id)}
                          disabled={forecastMutation.isPending}
                        >
                          <Sparkles className="h-3.5 w-3.5" />
                          AI Tahmin
                        </Button>
                      </div>
                    </TD>
                  </TR>
                ))}
                {!products.length && !productsQ.isLoading && (
                  <TR>
                    <TD colSpan={7} className="py-10 text-center text-ink-500">
                      Bu filtreye uygun ürün bulunamadı.
                    </TD>
                  </TR>
                )}
              </TBody>
            </Table>
          </CardContent>
        </Card>

        {forecast && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-sage-600" />
                AI Stok Tahmini —{" "}
                {products.find((p) => p.id === forecast.productId)?.name}
              </CardTitle>
              <Badge tone="sage">
                Güven: {Math.round(forecast.confidence * 100)}%
              </Badge>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-ink-700">
                {forecast.text}
              </p>
              {forecast.structured && (
                <pre className="mt-3 overflow-x-auto rounded-lg border border-cream-200 bg-cream-50 p-3 text-xs text-ink-600">
                  {JSON.stringify(forecast.structured, null, 2)}
                </pre>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </Shell>
  );
}
