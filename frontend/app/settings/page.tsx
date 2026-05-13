"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Trash2, Upload } from "lucide-react";
import { useRef, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { endpoints } from "@/lib/api";
import { ROLE_LABEL } from "@/lib/roles";
import { useAuthStore } from "@/lib/store";
import { formatRelative } from "@/lib/utils";

interface Doc {
  id: number;
  title: string;
  filename: string;
  category: string;
  chunk_count: number;
  size_bytes: number;
  created_at: string;
}

export default function SettingsPage() {
  const user = useAuthStore((s) => s.user);
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [title, setTitle] = useState("");

  const docsQ = useQuery<Doc[]>({
    queryKey: ["documents"],
    queryFn: endpoints.listDocuments,
  });

  const uploadMutation = useMutation({
    mutationFn: (vars: { file: File; title?: string }) =>
      endpoints.uploadDocument(vars.file, vars.title),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      setTitle("");
      if (fileRef.current) fileRef.current.value = "";
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => endpoints.deleteDocument(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });

  return (
    <Shell>
      <PageHeader
        title="Ayarlar"
        description="Hesap bilgileri ve AI bilgi tabanı belgeleri."
      />

      <div className="grid gap-4 p-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Hesabım</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Ad Soyad" value={user?.full_name ?? "—"} />
            <Row label="E-posta" value={user?.email ?? "—"} />
            <Row label="Rol" value={ROLE_LABEL[user?.role ?? ""] ?? "—"} />
            <Row label="Kimlik" value={`#${user?.id ?? "—"}`} />
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-sage-600" />
              AI Bilgi Tabanı
            </CardTitle>
            <Badge tone="sage">{docsQ.data?.length ?? 0} belge</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <form
              className="flex flex-col gap-2 rounded-xl border border-cream-200 bg-cream-50 p-4 md:flex-row"
              onSubmit={(e) => {
                e.preventDefault();
                const file = fileRef.current?.files?.[0];
                if (!file) return;
                uploadMutation.mutate({ file, title: title || undefined });
              }}
            >
              <Input
                ref={fileRef}
                type="file"
                accept=".pdf,.docx,.txt,.csv,.md"
                className="flex-1"
              />
              <Input
                placeholder="İsteğe bağlı başlık"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
              <Button type="submit" disabled={uploadMutation.isPending}>
                <Upload className="h-4 w-4" />
                Yükle
              </Button>
            </form>

            <ul className="space-y-2">
              {(docsQ.data ?? []).map((d) => (
                <li
                  key={d.id}
                  className="flex items-center justify-between rounded-xl border border-cream-200 bg-white px-4 py-3"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold text-ink-700">
                      {d.title}
                    </div>
                    <div className="truncate text-xs text-ink-500">
                      {d.filename} · {d.chunk_count} parça ·{" "}
                      {Math.round(d.size_bytes / 1024)} KB ·{" "}
                      {formatRelative(d.created_at)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge tone="muted">{d.category}</Badge>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => deleteMutation.mutate(d.id)}
                      title="Sil"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </li>
              ))}
              {!docsQ.data?.length && (
                <li className="rounded-xl border border-dashed border-cream-300 px-3 py-8 text-center text-xs text-ink-500">
                  Henüz belge yüklenmedi.
                </li>
              )}
            </ul>
          </CardContent>
        </Card>
      </div>
    </Shell>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-cream-200 pb-2 last:border-0 last:pb-0">
      <span className="text-xs font-semibold uppercase tracking-wide text-ink-400">
        {label}
      </span>
      <span className="text-ink-700">{value}</span>
    </div>
  );
}
