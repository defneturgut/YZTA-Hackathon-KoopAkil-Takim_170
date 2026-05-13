"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Info, Loader2, Plus, Sparkles } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Label, Modal, Select } from "@/components/ui/modal";
import { api, endpoints } from "@/lib/api";
import { formatRelative } from "@/lib/utils";

interface Task {
  id: number;
  title: string;
  description: string | null;
  status: "open" | "in_progress" | "done" | "cancelled";
  priority: "low" | "medium" | "high" | "critical";
  assignee_role: string;
  ai_generated: boolean;
  created_at: string;
}

const PRIORITY_TONES: Record<Task["priority"], "muted" | "sage" | "warning" | "danger"> = {
  low: "muted",
  medium: "sage",
  high: "warning",
  critical: "danger",
};

const PRIORITY_TR: Record<Task["priority"], string> = {
  low: "Düşük",
  medium: "Normal",
  high: "Yüksek",
  critical: "Çok Acil",
};

const STATUS_TR: Record<Task["status"], string> = {
  open: "Bekliyor",
  in_progress: "Devam Ediyor",
  done: "Tamamlandı",
  cancelled: "İptal",
};

const ROLE_TR: Record<string, string> = {
  warehouse: "Depo",
  courier: "Kurye",
  support: "Müşteri Destek",
  manager: "Yönetici",
  admin: "Yönetici",
};

export default function TasksPage() {
  const qc = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);

  const tasksQ = useQuery<Task[]>({
    queryKey: ["tasks"],
    queryFn: endpoints.listTasks,
  });

  const generateMutation = useMutation({
    mutationFn: endpoints.generateTasks,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const updateMutation = useMutation({
    mutationFn: (vars: { id: number; status: Task["status"] }) =>
      endpoints.updateTask(vars.id, { status: vars.status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const tasks = tasksQ.data ?? [];
  const grouped: Record<string, Task[]> = {
    open: tasks.filter((t) => t.status === "open"),
    in_progress: tasks.filter((t) => t.status === "in_progress"),
    done: tasks.filter((t) => t.status === "done"),
  };

  return (
    <Shell>
      <PageHeader
        title="Görevler"
        description="Manuel görev ekleyin veya AI'dan günlük operasyon planı oluşturmasını isteyin."
        actions={
          <>
            <Button variant="outline" size="md" onClick={() => setModalOpen(true)}>
              <Plus className="h-4 w-4" />
              Yeni Görev
            </Button>
            <Button
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
            >
              {generateMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              AI ile Plan Üret
            </Button>
          </>
        }
      />

      {/* ---- AI nasıl üretiyor bilgi şeridi ----------------------------- */}
      <div className="mx-6 mt-6 flex items-start gap-3 rounded-xl border border-sage-200 bg-sage-50/60 p-4 text-sm text-ink-700">
        <Info className="mt-0.5 h-5 w-5 shrink-0 text-sage-600" />
        <div>
          <div className="font-semibold text-ink-700">
            AI görevleri neye göre üretir?
          </div>
          <p className="mt-1 text-ink-600">
            AI plan üretirken (1) <b>kritik stok altındaki ürünleri</b>,
            (2) <b>geciken veya riskli kargoları</b>, ve (3) <b>açık operasyon
            görevlerini</b> inceler. Tedarikçi siparişi, müşteri bilgilendirme
            ve kargo rotalama için somut görevler oluşturur. Kafasına göre
            uydurmaz — sadece verilerde tespit edilen durumlara göre öneri
            sunar.
          </p>
        </div>
      </div>

      <div className="grid gap-4 p-6 lg:grid-cols-3">
        {(["open", "in_progress", "done"] as const).map((status) => (
          <Card key={status}>
            <CardHeader>
              <CardTitle>{STATUS_TR[status]}</CardTitle>
              <Badge tone="muted">{grouped[status].length}</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {grouped[status].map((t) => (
                <div
                  key={t.id}
                  className="rounded-xl border border-cream-200 bg-cream-50 p-4"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-semibold text-ink-700">{t.title}</div>
                    <Badge tone={PRIORITY_TONES[t.priority]}>
                      {PRIORITY_TR[t.priority]}
                    </Badge>
                  </div>
                  {t.description && (
                    <p className="mt-1.5 text-xs text-ink-500">{t.description}</p>
                  )}
                  <div className="mt-2.5 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5">
                      <Badge tone="muted">
                        {ROLE_TR[t.assignee_role] ?? t.assignee_role}
                      </Badge>
                      {t.ai_generated && <Badge tone="sage">AI</Badge>}
                    </div>
                    <span className="text-ink-400">
                      {formatRelative(t.created_at)}
                    </span>
                  </div>
                  {status !== "done" && (
                    <div className="mt-3 flex justify-end gap-1.5">
                      {status === "open" && (
                        <Button
                          size="sm"
                          variant="subtle"
                          onClick={() =>
                            updateMutation.mutate({
                              id: t.id,
                              status: "in_progress",
                            })
                          }
                        >
                          Başlat
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          updateMutation.mutate({ id: t.id, status: "done" })
                        }
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Bitti
                      </Button>
                    </div>
                  )}
                </div>
              ))}
              {!grouped[status].length && (
                <div className="rounded-xl border border-dashed border-cream-300 px-3 py-8 text-center text-xs text-ink-400">
                  Boş 🌿
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <NewTaskModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={() => {
          qc.invalidateQueries({ queryKey: ["tasks"] });
          setModalOpen(false);
        }}
      />
    </Shell>
  );
}

/* ---------------------------------------------------------------- */
function NewTaskModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<Task["priority"]>("medium");
  const [assigneeRole, setAssigneeRole] = useState("warehouse");
  const [relatedOrderCode, setRelatedOrderCode] = useState("");
  const [relatedSku, setRelatedSku] = useState("");
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        title,
        description: description || undefined,
        priority,
        assignee_role: assigneeRole,
        related_order_code: relatedOrderCode || undefined,
        related_sku: relatedSku || undefined,
      };
      return api.post("/tasks", payload).then((r) => r.data);
    },
    onSuccess: () => {
      setTitle("");
      setDescription("");
      setPriority("medium");
      setAssigneeRole("warehouse");
      setRelatedOrderCode("");
      setRelatedSku("");
      setError(null);
      onCreated();
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Görev oluşturulamadı.";
      setError(detail);
    },
  });

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Yeni Görev Oluştur"
      description="Manuel görev ekleyin. AI üretmediği halde takip edilmesi gereken işler için idealdir."
      size="md"
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!title.trim()) {
            setError("Görev başlığı zorunludur.");
            return;
          }
          createMutation.mutate();
        }}
        className="space-y-4"
      >
        <div className="space-y-1.5">
          <Label htmlFor="title">Görev Başlığı *</Label>
          <Input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Örn: Tedarikçi Anadolu Tarım ile telefon görüşmesi"
            required
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="description">Açıklama (opsiyonel)</Label>
          <Textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Detayları yazın…"
            rows={3}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="priority">Öncelik</Label>
            <Select
              id="priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value as Task["priority"])}
            >
              <option value="low">Düşük</option>
              <option value="medium">Normal</option>
              <option value="high">Yüksek</option>
              <option value="critical">Çok Acil</option>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="assignee">Atanacak Rol</Label>
            <Select
              id="assignee"
              value={assigneeRole}
              onChange={(e) => setAssigneeRole(e.target.value)}
            >
              <option value="warehouse">Depo</option>
              <option value="courier">Kurye</option>
              <option value="support">Müşteri Destek</option>
              <option value="manager">Yönetici</option>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="order">Sipariş Kodu (opsiyonel)</Label>
            <Input
              id="order"
              value={relatedOrderCode}
              onChange={(e) => setRelatedOrderCode(e.target.value)}
              placeholder="AEG-01005"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="sku">Ürün SKU (opsiyonel)</Label>
            <Input
              id="sku"
              value={relatedSku}
              onChange={(e) => setRelatedSku(e.target.value)}
              placeholder="DMS-001"
            />
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            İptal
          </Button>
          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Oluşturuluyor…
              </>
            ) : (
              <>
                <Plus className="h-4 w-4" />
                Görevi Oluştur
              </>
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
