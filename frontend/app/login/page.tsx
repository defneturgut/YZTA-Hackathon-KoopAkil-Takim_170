"use client";

import { Leaf, Loader2, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/modal";
import { endpoints } from "@/lib/api";
import { defaultLandingFor, ROLE_DESCRIPTION, ROLE_LABEL } from "@/lib/roles";
import { useAuthStore } from "@/lib/store";

const DEMO_ACCOUNTS: { role: string; email: string }[] = [
  { role: "manager", email: "yonetici@koopakil.tr" },
  { role: "warehouse", email: "depo@koopakil.tr" },
  { role: "courier", email: "kurye@koopakil.tr" },
  { role: "support", email: "destek@koopakil.tr" },
  { role: "customer", email: "musteri@koopakil.tr" },
];

export default function LoginPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const [email, setEmail] = useState("yonetici@aegis-kobi.tr");
  const [password, setPassword] = useState("admin1234");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await endpoints.login(email, password);
      setTokens(data.access_token, data.refresh_token, data.user);
      router.push(defaultLandingFor(data.user?.role));
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Giriş yapılamadı. Bilgileri kontrol edin.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen bg-cream-50 lg:grid-cols-2">
      {/* ---- Sol panel — marka -------------------------------------- */}
      <div className="relative hidden flex-col justify-between overflow-hidden border-r border-cream-200 bg-leaf-fade p-12 lg:flex">
        <div className="flex items-center gap-3">
          <div className="grid h-12 w-12 place-items-center rounded-2xl bg-sage-100 text-sage-600">
            <Leaf className="h-6 w-6" />
          </div>
          <div>
            <div className="text-lg font-bold tracking-tight text-ink-700">
              KoopAkıl
            </div>
            <div className="text-xs text-ink-500">
              Kooperatifler için AI destekli operasyon
            </div>
          </div>
        </div>

        <div className="max-w-md space-y-6">
          <h2 className="text-3xl font-bold leading-tight text-ink-700">
            Üreticinin yanında, müşterinin yakınında.
          </h2>
          <p className="text-base text-ink-500">
            Siparişlerinizi, stoklarınızı ve kargonuzu tek bir sade ekrandan
            yönetin. Yapay zeka asistanınız soruları yanıtlar, riskleri sizden
            önce fark eder.
          </p>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              { t: "Siparişler", d: "Otomatik takip" },
              { t: "Stoklar", d: "Akıllı uyarı" },
              { t: "Kargolar", d: "Gecikme bildirimi" },
              { t: "AI Asistan", d: "7/24 yardım" },
            ].map((f) => (
              <div
                key={f.t}
                className="rounded-xl border border-cream-200 bg-white/80 px-4 py-3"
              >
                <div className="text-sm font-semibold text-ink-700">{f.t}</div>
                <div className="text-xs text-ink-500">{f.d}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-ink-500">
          <ShieldCheck className="h-4 w-4 text-sage-500" />
          Verileriniz güvende — yerel sunucunuzda saklanır.
        </div>
      </div>

      {/* ---- Sağ panel — form --------------------------------------- */}
      <div className="flex items-center justify-center px-6 py-12">
        <Card className="w-full max-w-md p-8">
          <CardContent className="space-y-6 p-0">
            <div>
              <h1 className="text-2xl font-bold text-ink-700">
                Hoş geldiniz 👋
              </h1>
              <p className="mt-1 text-sm text-ink-500">
                Operasyon merkezinize erişmek için giriş yapın.
              </p>
            </div>

            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email">E-posta</Label>
                <Input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ornek@aegis-kobi.tr"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">Şifre</Label>
                <Input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>

              {error && (
                <div className="rounded-lg border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                size="lg"
                className="w-full"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Giriş yapılıyor…
                  </>
                ) : (
                  "Giriş Yap"
                )}
              </Button>
            </form>

            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-400">
                Demo hesaplar
              </div>
              <div className="grid grid-cols-2 gap-2">
                {DEMO_ACCOUNTS.map((acc) => (
                  <Button
                    key={acc.email}
                    type="button"
                    variant="subtle"
                    size="sm"
                    onClick={() => {
                      setEmail(acc.email);
                      setPassword("admin1234");
                    }}
                    className="h-auto py-2"
                  >
                    <div className="flex flex-col items-start text-left">
                      <span className="text-sm font-semibold">
                        {ROLE_LABEL[acc.role]}
                      </span>
                      <span className="text-[10px] font-normal opacity-80">
                        {ROLE_DESCRIPTION[acc.role]}
                      </span>
                    </div>
                  </Button>
                ))}
              </div>
              <div className="mt-3 rounded-lg bg-cream-50 px-3 py-2 text-xs text-ink-500">
                💡 Tüm demo hesaplar için şifre:{" "}
                <span className="font-mono font-semibold text-sage-700">
                  admin1234
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
