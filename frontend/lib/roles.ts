/**
 * Rol bazlı erişim haritası — KoopAkıl.
 *
 *   • admin / manager  → tüm operasyon merkezi
 *   • warehouse        → görevler + envanter (sade)
 *   • courier          → kargolar + günlük rota (sade)
 *   • support          → AI Asistan + müşteri sorguları + uyarılar
 *   • customer         → SADECE kendi sipariş & kargo geçmişi
 *
 * Sidebar bu listeyi kullanıcının rolüne göre filtreler.
 */

export type AppRole =
  | "admin"
  | "manager"
  | "warehouse"
  | "courier"
  | "support"
  | "customer";

export interface NavRoute {
  href: string;
  label: string;
  description: string;
  iconKey:
    | "home"
    | "chat"
    | "boxes"
    | "truck"
    | "tasks"
    | "alert"
    | "chart"
    | "settings"
    | "user";
  allowedRoles: AppRole[];
}

export const NAV_ROUTES: NavRoute[] = [
  // ---- Müşteri'ye özel (önce gelsin ki üstte görünsün) ----
  {
    href: "/portal",
    label: "Siparişlerim",
    description: "Geçmiş ve aktif siparişler",
    iconKey: "boxes",
    allowedRoles: ["customer"],
  },
  {
    href: "/portal/shipments",
    label: "Kargolarım",
    description: "Teslimat takibi",
    iconKey: "truck",
    allowedRoles: ["customer"],
  },

  // ---- Çalışanlar için ----
  {
    href: "/dashboard",
    label: "Ana Sayfa",
    description: "Günün özeti",
    iconKey: "home",
    allowedRoles: ["admin", "manager", "warehouse", "courier", "support"],
  },
  {
    href: "/chat",
    label: "AI Asistan",
    description: "Sorularınızı sorun",
    iconKey: "chat",
    allowedRoles: ["admin", "manager", "support"],
  },
  {
    href: "/inventory",
    label: "Envanter",
    description: "Stok takibi",
    iconKey: "boxes",
    allowedRoles: ["admin", "manager", "warehouse"],
  },
  {
    href: "/shipments",
    label: "Kargolar",
    description: "Gönderiler ve teslimat",
    iconKey: "truck",
    allowedRoles: ["admin", "manager", "courier", "support"],
  },
  {
    href: "/tasks",
    label: "Görevler",
    description: "İşlerim",
    iconKey: "tasks",
    allowedRoles: ["admin", "manager", "warehouse", "courier"],
  },
  {
    href: "/alerts",
    label: "Uyarılar",
    description: "Bildirimler",
    iconKey: "alert",
    allowedRoles: ["admin", "manager", "warehouse", "support"],
  },
  {
    href: "/analytics",
    label: "Analitik",
    description: "Raporlar",
    iconKey: "chart",
    allowedRoles: ["admin", "manager"],
  },
  {
    href: "/settings",
    label: "Ayarlar",
    description: "Hesap & bilgi tabanı",
    iconKey: "settings",
    allowedRoles: ["admin", "manager", "warehouse", "courier", "support", "customer"],
  },
];

/** Kullanıcı login olduğunda nereye yönlendirileceği. */
export function defaultLandingFor(role: string | undefined): string {
  switch (role) {
    case "customer":
      return "/portal";
    case "warehouse":
      return "/tasks";
    case "courier":
      return "/shipments";
    case "support":
      return "/chat";
    default:
      return "/dashboard";
  }
}

export const ROLE_LABEL: Record<string, string> = {
  admin: "Yönetici",
  manager: "Yönetici",
  warehouse: "Depo Görevlisi",
  courier: "Kurye",
  support: "Müşteri Destek",
  customer: "Müşteri",
};

export const ROLE_DESCRIPTION: Record<string, string> = {
  admin: "Tüm operasyonları yönetir",
  manager: "Operasyonları planlar ve analiz eder",
  warehouse: "Sipariş hazırlar, stok kontrolü yapar",
  courier: "Kargoları teslim eder",
  support: "Müşteri sorularını yanıtlar",
  customer: "Siparişlerini ve kargolarını takip eder",
};
