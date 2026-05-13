"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCircle2 } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { endpoints } from "@/lib/api";
import { formatRelative } from "@/lib/utils";

interface Alert {
  id: number;
  title: string;
  message: string;
  category: string;
  severity: "info" | "warning" | "high" | "critical";
  is_read: boolean;
  is_resolved: boolean;
  source: string;
  created_at: string;
}

const TONES: Record<Alert["severity"], "sage" | "info" | "warning" | "danger"> = {
  info: "info",
  warning: "warning",
  high: "danger",
  critical: "danger",
};

const SEVERITY_TR: Record<Alert["severity"], string> = {
  info: "Bilgi",
  warning: "Uyarı",
  high: "Önemli",
  critical: "Acil",
};

export default function AlertsPage() {
  const qc = useQueryClient();
  const alertsQ = useQuery<Alert[]>({
    queryKey: ["alerts"],
    queryFn: endpoints.listAlerts,
  });

  const markRead = useMutation({
    mutationFn: (id: number) => endpoints.markAlertRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const resolve = useMutation({
    mutationFn: (id: number) => endpoints.resolveAlert(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const alerts = alertsQ.data ?? [];
  const unread = alerts.filter((a) => !a.is_read).length;

  return (
    <Shell>
      <PageHeader
        title="Uyarılar"
        description="AI ve sistem tarafından üretilen bildirimler."
        actions={<Badge tone="warning">{unread} okunmamış</Badge>}
      />

      <div className="space-y-3 p-6">
        {alerts.map((a) => (
          <Card key={a.id} className={a.is_read ? "opacity-70" : ""}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-sage-600" />
                {a.title}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Badge tone={TONES[a.severity]}>{SEVERITY_TR[a.severity]}</Badge>
                <Badge tone="muted">{a.source}</Badge>
                <span className="text-xs text-ink-500">
                  {formatRelative(a.created_at)}
                </span>
              </div>
            </CardHeader>
            <CardContent className="flex items-start justify-between gap-4">
              <p className="text-sm text-ink-700">{a.message}</p>
              <div className="flex gap-1.5">
                {!a.is_read && (
                  <Button
                    size="sm"
                    variant="subtle"
                    onClick={() => markRead.mutate(a.id)}
                  >
                    Okundu
                  </Button>
                )}
                {!a.is_resolved && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => resolve.mutate(a.id)}
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Çözüldü
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
        {!alerts.length && !alertsQ.isLoading && (
          <Card className="p-10 text-center text-sm text-ink-500">
            Şu anda görüntülenecek uyarı yok 🌿
          </Card>
        )}
      </div>
    </Shell>
  );
}
