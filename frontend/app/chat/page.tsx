"use client";

import { useMutation } from "@tanstack/react-query";
import { Leaf, Send, Sparkles, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";

import { PageHeader } from "@/components/page-header";
import { Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/input";
import { endpoints } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  confidence?: number;
  sources?: { label: string; reference: string; excerpt?: string; type?: string }[];
  toolCalls?: { tool: string }[];
  latencyMs?: number;
}

const STARTERS = [
  "Siparişim ne zaman gelir?",
  "Hangi ürünlerin stoğu azaldı?",
  "Bugün için operasyon planı çıkar.",
  "Geciken kargoları analiz et.",
];

export default function ChatPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "intro",
      role: "assistant",
      content:
        "Merhaba 🌿 Ben **KoopAkıl Asistanı**.\n\nMüşteri sorularına yanıt verebilir, **kargo & stok analizleri** üretebilir ve **operasyon planı** çıkarabilirim.\n\nAşağıdaki örneklerden birine tıklayın veya kendi sorunuzu yazın.",
      confidence: 1,
    },
  ]);
  const endRef = useRef<HTMLDivElement>(null);

  const sendMutation = useMutation({
    mutationFn: (message: string) => endpoints.sendMessage(message, sessionId),
    onSuccess: (data) => {
      setSessionId(data.session_id);
      setMessages((m) => [
        ...m,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: data.message,
          confidence: data.confidence,
          sources: data.sources,
          toolCalls: data.tool_calls,
          latencyMs: data.latency_ms,
        },
      ]);
    },
    onError: (err: unknown) => {
      // Backend artık her durumda 200 dönüyor olmalı; yine de
      // network kopması / 502 / CORS gibi durumlar için zarif düşüş.
      const e = err as {
        response?: { status?: number; data?: { detail?: string } };
        message?: string;
      };
      const detail =
        e?.response?.data?.detail ||
        e?.message ||
        "Sunucuya ulaşılamadı.";
      const status = e?.response?.status;
      setMessages((m) => [
        ...m,
        {
          id: `error-${Date.now()}`,
          role: "assistant",
          content:
            `⚠️ **Yanıt alınamadı.**\n\n` +
            (status ? `HTTP ${status} — ` : "") +
            `${detail}\n\n` +
            `Lütfen:\n` +
            `1. Backend'in çalıştığından emin olun (\`docker compose ps\`)\n` +
            `2. Sağ üstteki AI rozeti **Gemini bağlı** mı kontrol edin\n` +
            `3. \`/health/ai\` endpoint'ini test edin`,
          confidence: 0,
        },
      ]);
    },
  });

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sendMutation.isPending]);

  function submit(text: string) {
    if (!text.trim()) return;
    setMessages((m) => [
      ...m,
      { id: `user-${Date.now()}`, role: "user", content: text },
    ]);
    setInput("");
    sendMutation.mutate(text);
  }

  return (
    <Shell>
      <PageHeader
        title="AI Asistan"
        description="Müşteri sorularınızı yanıtlayan ve operasyonları analiz eden yapay zeka."
        actions={
          <Badge tone="sage">
            <Sparkles className="h-3 w-3" />
            Bilgi tabanı + Araçlar
          </Badge>
        }
      />

      <div className="flex h-[calc(100vh-3.5rem-100px)] flex-col gap-4 p-6">
        <Card className="flex flex-1 flex-col overflow-hidden">
          {/* ---- Mesaj akışı ------------------------------------------- */}
          <div className="flex-1 space-y-4 overflow-y-auto p-6">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {sendMutation.isPending && <ThinkingBubble />}
            <div ref={endRef} />
          </div>

          {/* ---- Hızlı başlangıç butonları ----------------------------- */}
          {messages.length === 1 && (
            <div className="border-t border-cream-200 px-6 py-3">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-400">
                Hızlı sorular
              </div>
              <div className="flex flex-wrap gap-2">
                {STARTERS.map((s) => (
                  <Button
                    key={s}
                    variant="subtle"
                    size="sm"
                    onClick={() => submit(s)}
                  >
                    {s}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* ---- Yazma alanı ------------------------------------------- */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit(input);
            }}
            className="flex items-end gap-2 border-t border-cream-200 p-4"
          >
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit(input);
                }
              }}
              placeholder="Mesajınızı buraya yazın…"
              className="min-h-[48px] flex-1 resize-none"
            />
            <Button
              type="submit"
              size="lg"
              disabled={sendMutation.isPending || !input.trim()}
            >
              <Send className="h-4 w-4" />
              Gönder
            </Button>
          </form>
        </Card>
      </div>
    </Shell>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex gap-3 animate-fadeUp", isUser && "justify-end")}>
      {!isUser && (
        <div className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-full bg-sage-100 text-sage-600">
          <Leaf className="h-4 w-4" />
        </div>
      )}
      <div
        className={cn(
          "max-w-[78%] space-y-2 rounded-2xl border px-4 py-3 text-sm leading-relaxed shadow-soft",
          isUser
            ? "border-sage-200 bg-sage-50 text-ink-700"
            : "border-cream-200 bg-white text-ink-700",
        )}
      >
        <div className="prose-chat">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        {!isUser && (message.sources?.length || message.toolCalls?.length) ? (
          <div className="mt-2 border-t border-cream-200 pt-2 text-xs text-ink-500">
            {message.toolCalls?.length ? (
              <div className="mb-1.5">
                <span className="mr-1 font-semibold text-ink-600">
                  Kullandığım araçlar:
                </span>
                {message.toolCalls.map((t, i) => (
                  <Badge key={`${t.tool}-${i}`} tone="sage" className="mr-1">
                    {t.tool}
                  </Badge>
                ))}
              </div>
            ) : null}
            {message.sources?.length ? (
              <div className="space-y-1">
                <div className="font-semibold text-ink-600">Kaynaklar:</div>
                <ol className="ml-4 list-decimal space-y-0.5">
                  {message.sources.map((s, idx) => (
                    <li key={`${s.reference}-${idx}`}>
                      <span className="font-medium text-ink-700">{s.label}</span>
                      {s.excerpt ? (
                        <span className="ml-1 text-ink-500">
                          — {s.excerpt.slice(0, 110)}
                          {s.excerpt.length > 110 ? "…" : ""}
                        </span>
                      ) : null}
                    </li>
                  ))}
                </ol>
              </div>
            ) : null}
          </div>
        ) : null}
        {!isUser && message.confidence != null && message.id !== "intro" ? (
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-wide text-ink-400">
            <span>Güven: {Math.round(message.confidence * 100)}%</span>
            {message.latencyMs ? <span>• {message.latencyMs} ms</span> : null}
          </div>
        ) : null}
      </div>
      {isUser && (
        <div className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-full bg-earth-100 text-earth-500">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}

function ThinkingBubble() {
  return (
    <div className="flex gap-3 animate-fadeUp">
      <div className="mt-0.5 grid h-9 w-9 place-items-center rounded-full bg-sage-100 text-sage-600">
        <Leaf className="h-4 w-4" />
      </div>
      <div className="rounded-2xl border border-cream-200 bg-white px-4 py-3 shadow-soft">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 animate-pulseDot rounded-full bg-sage-500" />
          <span
            className="h-2 w-2 animate-pulseDot rounded-full bg-sage-500"
            style={{ animationDelay: "0.2s" }}
          />
          <span
            className="h-2 w-2 animate-pulseDot rounded-full bg-sage-500"
            style={{ animationDelay: "0.4s" }}
          />
        </div>
      </div>
    </div>
  );
}
