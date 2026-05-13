"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { defaultLandingFor } from "@/lib/roles";
import { useAuthStore } from "@/lib/store";

export default function Home() {
  const router = useRouter();
  const token = useAuthStore((s) => s.accessToken);
  const role = useAuthStore((s) => s.user?.role);

  useEffect(() => {
    if (!token) {
      router.replace("/login");
    } else {
      router.replace(defaultLandingFor(role));
    }
  }, [router, token, role]);

  return (
    <div className="grid min-h-screen place-items-center bg-cream-50 text-ink-500">
      <div className="flex items-center gap-3 text-sm">
        <span className="grid h-2 w-2 place-items-center rounded-full bg-sage-500 animate-pulseDot" />
        Yönlendiriliyor…
      </div>
    </div>
  );
}
