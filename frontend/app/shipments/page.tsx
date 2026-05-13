"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldAlert, Sparkles, Truck } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TBody, TD, TH, THead, TR, Table } from "@/components/ui/table";
import { endpoints } from "@/lib/api";
import { formatRelative } from "@/lib/utils";

interface Shipment {
  id: number;
  tracking_code: string;
  carrier: string;
  origin_city: string;
  destination_city: string;
  current_location: string;
  status: string;
  risk_score: number;
  ai_summary: string | null;
  updated_at: string;
}

const STATUS_TONES: Record<string, "info" | "success" | "warning" | "danger" | "muted" | "sage"> = {
  created: "muted",
  picked_up: "info",
  in_transit: "info",
  at_hub: "info",
  out_for_delivery: "sage",
  delivered: "success",
  delayed: "warning",
  exception: "danger",
};

const STATUS_TR: Record<string, string> = {
  created: "Hazırlanıyor",
  picked_up: "Teslim Alındı",
  in_transit: "Yolda",
  at_hub: "Merkezde",
  out_for_delivery: "Dağıtımda",
  delivered: "Teslim Edildi",
  delayed: "Gecikti",
  exception: "Sorunlu",
};

export default function ShipmentsPage() {
  const qc = useQueryClient();
  const [analysis, setAnalysis] = useState<{
    code: string;
    risk_level: string;
    reason: string;
    recommended_action: string;
    confidence_score: number;
  } | null>(null);

  const shipmentsQ = useQuery<Shipment[]>({
    queryKey: ["shipments"],
    queryFn: endpoints.listShipments,
  });

  const checkMutation = useMutation({
    mutationFn: (id: number) => endpoints.checkShipment(id),
    onSuccess: (data) => {
      setAnalysis({
        code: data.tracking_code,
        risk_level: data.risk_level,
        reason: data.reason,
        recommended_action: data.recommended_action,
        confidence_score: data.confidence_score,
      });
      qc.invalidateQueries({ queryKey: ["shipments"] });
    },
  });

  const shipments = shipmentsQ.data ?? [];
  const delayed = shipments.filter(
    (s) => s.status === "delayed" || s.status === "exception",
  ).length;

  return (
    <Shell>
      <PageHeader
        title="Kargolar"
        description="Aktif kargo trafiğinizi takip edin; AI ile gecikme ve risk analizi yapın."
        actions={
          <Badge tone={delayed ? "warning" : "sage"}>
            <ShieldAlert className="h-3 w-3" />
            {delayed} kargo dikkat istiyor
          </Badge>
        }
      />

      <div className="space-y-6 p-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Truck className="h-4 w-4 text-sage-600" />
              Aktif Kargolar
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <THead>
                <TR>
                  <TH>Takip Kodu</TH>
                  <TH>Taşıyıcı</TH>
                  <TH>Güzergah</TH>
                  <TH>Konum</TH>
                  <TH>Durum</TH>
                  <TH>Risk</TH>
                  <TH>Son Güncelleme</TH>
                  <TH className="text-right">AI</TH>
                </TR>
              </THead>
              <TBody>
                {shipments.map((s) => (
                  <TR key={s.id}>
                    <TD className="font-mono text-xs">{s.tracking_code}</TD>
                    <TD>{s.carrier}</TD>
                    <TD className="text-ink-500">
                      {s.origin_city} → {s.destination_city}
                    </TD>
                    <TD>{s.current_location}</TD>
                    <TD>
                      <Badge tone={STATUS_TONES[s.status] ?? "muted"}>
                        {STATUS_TR[s.status] ?? s.status}
                      </Badge>
                    </TD>
                    <TD>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-24 overflow-hidden rounded-full bg-cream-200">
                          <div
                            className="h-full bg-gradient-to-r from-sage-400 via-warning to-danger"
                            style={{ width: `${Math.round(s.risk_score * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-ink-500">
                          {Math.round(s.risk_score * 100)}%
                        </span>
                      </div>
                    </TD>
                    <TD className="text-xs text-ink-500">
                      {formatRelative(s.updated_at)}
                    </TD>
                    <TD className="text-right">
                      <Button
                        size="sm"
                        variant="subtle"
                        onClick={() => checkMutation.mutate(s.id)}
                        disabled={checkMutation.isPending}
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                        Analiz Et
                      </Button>
                    </TD>
                  </TR>
                ))}
                {!shipments.length && !shipmentsQ.isLoading && (
                  <TR>
                    <TD colSpan={8} className="py-10 text-center text-ink-500">
                      Şu an aktif kargo yok.
                    </TD>
                  </TR>
                )}
              </TBody>
            </Table>
          </CardContent>
        </Card>

        {analysis && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-sage-600" />
                AI Anomali Analizi — {analysis.code}
              </CardTitle>
              <Badge
                tone={
                  analysis.risk_level === "high" || analysis.risk_level === "critical"
                    ? "danger"
                    : analysis.risk_level === "medium"
                      ? "warning"
                      : "sage"
                }
              >
                Risk: {analysis.risk_level}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-ink-700">
              <div>
                <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-400">
                  Tespit
                </div>
                {analysis.reason}
              </div>
              <div>
                <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-400">
                  Önerilen Aksiyon
                </div>
                {analysis.recommended_action}
              </div>
              <div className="text-xs text-ink-500">
                Güven skoru: {Math.round(analysis.confidence_score * 100)}%
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Shell>
  );
}
