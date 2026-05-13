import type { Metadata } from "next";
import "./globals.css";

import { Providers } from "@/lib/providers";

export const metadata: Metadata = {
  title: "KoopAkıl — Kooperatifinizin Akıllı Yardımcısı",
  description:
    "Tarım kooperatifleri ve KOBİ'ler için yapay zeka destekli müşteri destek, kargo, stok ve operasyon yönetim platformu.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className="min-h-screen antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
