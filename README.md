# 🌿 KoopAkıl — Kooperatifinizin Akıllı Yardımcısı

> Üretici kooperatifleri ve KOBİ'ler için **Gemini AI destekli** uçtan
> uca operasyon platformu. Müşteri destek, kargo lojistiği, akıllı stok
> yönetimi ve günlük operasyon planlamasını tek bir sade arayüzde
> birleştirir.

[![Python](https://img.shields.io/badge/python-3.12-3776AB?style=flat-square)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square)](https://nextjs.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Pro-4285F4?style=flat-square)](https://ai.google.dev/)

---

## İçindekiler

1. [Hızlı Bakış](#hızlı-bakış)
2. [Hedef Kullanıcı & Tasarım Felsefesi](#hedef-kullanıcı--tasarım-felsefesi)
3. [Rol-Bazlı Deneyim](#rol-bazlı-deneyim)
4. [Mimari](#mimari)
5. [Modüller](#modüller)
6. [Hızlı Başlangıç](#hızlı-başlangıç)
7. [⚙️ Gerçek Gemini API'ye Geçiş & Sorun Giderme](#️-gerçek-gemini-apiye-geçiş--sorun-giderme)
8. [💾 Veri Kalıcılığı](#-veri-kalıcılığı)
9. [AI Görev Üretimi — Nasıl Çalışır?](#ai-görev-üretimi--nasıl-çalışır)
10. [AI Yaklaşımı](#ai-yaklaşımı)
11. [API Referansı](#api-referansı)
12. [Klasör Yapısı](#klasör-yapısı)
13. [Production Deployment](#production-deployment)

---

## Hızlı Bakış

| Yön | Detay |
| --- | --- |
| **Proje** | KoopAkıl |
| **Hedef Kitle** | Tarım/el sanatları kooperatifleri, küçük e-ticaret |
| **Ana Yetenek** | Multi-tool AI ajan + RAG + anomali tespiti + günlük brifing + manuel + AI görev üretimi + müşteri portalı |
| **Stack** | FastAPI · SQLAlchemy 2.0 · Next.js 15 · Tailwind · Recharts |
| **AI** | Google **Gemini 2.5 Pro** + Embeddings + Function Calling |
| **Tasarım** | Açık tema · doğal yeşil/krem palet · sade tipografi |
| **Modlar** | Demo (mock, key gerekmez) · Production (gerçek Gemini key ile) |

---

## Hedef Kullanıcı & Tasarım Felsefesi

KoopAkıl, **20–200 ürünlük tarım kooperatifleri ve butik üreticileri**
hedefler. Çalışanların büyük kısmı teknik değildir — bu yüzden:

- 🤍 **Beyaz zemin + soft yeşil/krem** — gözü yormaz, doğa hissi verir
- 🌿 **Büyük tipografi, geniş boşluk, ikon destekli butonlar**
- 🇹🇷 **Tüm UI Türkçe** — teknik jargon yerine günlük dil
- 🪜 **Rol bazlı sadelik** — bir depo görevlisi yönetim panelini görmez
- 💚 **Yardımcı mesajlar** — "Bugün hazırlanacak paketler", "Stoğu azalan ürünler"

---

## Rol-Bazlı Deneyim

Her kullanıcı rolüne uygun bir ekran açılır. Sidebar otomatik filtrelenir.

| Rol | Giriş Sonrası | Sidebar İçeriği |
| --- | --- | --- |
| **Yönetici / Admin** | `/dashboard` | Tümü |
| **Depo Görevlisi** | `/tasks` ("Bugün hazırlanacak paketler") | Ana Sayfa · Envanter · Görevler · Uyarılar · Ayarlar |
| **Kurye** | `/shipments` ("Bugünkü rotanız") | Ana Sayfa · Kargolar · Görevler · Ayarlar |
| **Müşteri Destek** | `/chat` (AI Asistan) | Ana Sayfa · AI Asistan · Kargolar · Uyarılar · Ayarlar |
| **Müşteri** 🆕 | `/portal` (Siparişlerim) | Siparişlerim · Kargolarım · Ayarlar |

> Müşteri rolündeki kullanıcı **sadece kendi** sipariş ve kargolarını
> görür — backend `Order.customer_email` üzerinden filtreler. Yönetim
> ekranlarına erişimi yoktur.

---

## Mimari

```text
┌──────────────────────────────────────────────────────────────────┐
│                       KoopAkıl Platform                          │
└──────────────────────────────────────────────────────────────────┘
   ┌──────────────┐         ┌────────────────────────────────────┐
   │   Browser    │ ──HTTP─▶│         Nginx Reverse Proxy        │
   └──────────────┘         │   (rate-limit · security headers)  │
                            └────────┬───────────────────┬───────┘
                                     │                   │
                            ┌────────▼────────┐  ┌───────▼────────┐
                            │   FastAPI 0.115 │  │   Next.js 15   │
                            │   (async, JWT)  │  │   (Tailwind)   │
                            └─────┬─────┬─────┘  └────────────────┘
                                  │     │
            ┌─────────────────────┘     └─────────────────────┐
            │                                                 │
   ┌────────▼─────────┐                            ┌──────────▼────────┐
   │   AI Layer       │                            │  Persistence      │
   │  • Gemini svc    │                            │  • PostgreSQL     │
   │  • RAG pipeline  │                            │  • Redis (memory) │
   │  • Ops Agent     │                            └───────────────────┘
   │  • 4 Tools       │
   └──────────────────┘
```

---

## Modüller

### Modül 1 — AI Müşteri Destek Merkezi
- Web chat, multi-turn Türkçe, Redis tabanlı session memory
- **RAG**: PDF/DOCX/TXT/CSV yükleme → chunking → Gemini embeddings → cosine retrieval → grounded response
- Kaynak alıntıları + güven skoru + halüsinasyon azaltma

### Modül 2 — Kargo & Lojistik AI
- Shipment tracking + event log
- **AI anomali tespiti**: 48+ saat duraksama, transit gecikmesi, yüksek riskli teslimat

### Modül 3 — Akıllı Stok Yönetimi
- Low-stock tespiti + canlı KPI'lar
- AI predictive forecast: tükenme tarihi + önerilen sipariş miktarı

### Modül 4 — Günlük Operasyon Ajanı
- **Multi-tool agent**: 4 tool + Gemini reasoning + structured outputs
- **Manuel + AI görev üretimi**

### Modül 5 — Müşteri Portalı 🆕
- Müşteri kendi sipariş ve kargolarını görür
- Kargo timeline'ı (her event/durum adımı)

---

## Hızlı Başlangıç

### Docker ile tek komut

```bash
git clone <repo>
cd YZTA-Hackathon
cp .env.example .env
docker compose up --build
```

Sonra:
- 🌐 Frontend: <http://localhost:3000>
- ⚙️ Backend Swagger: <http://localhost:8000/docs>
- 🩺 AI sağlık kontrolü: <http://localhost:8000/health/ai>

### Demo Hesapları

| Rol | E-posta | Şifre |
| --- | --- | --- |
| Admin | `admin@koopakil.tr` | `admin1234` |
| Yönetici | `yonetici@koopakil.tr` | `admin1234` |
| Depo | `depo@koopakil.tr` | `admin1234` |
| Kurye | `kurye@koopakil.tr` | `admin1234` |
| Destek | `destek@koopakil.tr` | `admin1234` |
| **Müşteri** | `musteri@koopakil.tr` | `admin1234` |

> Demo müşterisi `Zeynep Aydın`'a seed sırasında ilk 5 sipariş atanır,
> böylece müşteri panelinde dolu bir geçmiş görünür.

---

## ⚙️ Gerçek Gemini API'ye Geçiş & Sorun Giderme

### Tek kural: **API key varsa, gerçek Gemini kullanılır.**

`.env` dosyanıza geçerli bir key ekleyin ve backend'i restart edin:

```env
GEMINI_API_KEY=AIzaSy....   # https://ai.google.dev'den ücretsiz alın
GEMINI_MODEL=gemini-2.5-pro
```

```bash
docker compose restart backend
```

Backend log'unda şu satırı görmelisiniz:
```
✅ AI backend: REAL Gemini (model=gemini-2.5-pro) — key configured
```

### 🐛 "API key koydum ama AI yine mock yanıt veriyor"

1. **Key formatı yanlış** → geçerli key `AIza` ile başlar, > 20 karakter
   ```bash
   docker compose exec backend env | grep GEMINI_API_KEY
   ```

2. **Backend restart edilmedi** → `.env` değişikliği sadece restart ile
   geçerli olur:
   ```bash
   docker compose restart backend
   ```

3. **AI sağlığını test edin** → kapsamlı debug endpoint:
   ```bash
   curl http://localhost:8000/health/ai
   ```
   Çalışıyorken:
   ```json
   {
     "backend": "gemini",
     "model": "gemini-2.5-pro",
     "key_configured": true,
     "key_looks_valid": true,
     "ok": true,
     "sample_response": "KoopAkıl AI hazır.",
     "latency_ms": 450
   }
   ```
   Sorun varsa `last_error` alanı hatayı söyler.

4. **Quota / billing** → Gemini'nin ücretsiz tier'ı 60 RPM. Aşıldıysa
   sistem **otomatik mock'a düşer** (uygulamanın çökmemesi için).

### Mock modunu zorla
Key olsa bile mock'a düşmek için `.env`'de `GEMINI_API_KEY=` (boş).

---

## 💾 Veri Kalıcılığı

> "Envanterde değiştirdiğim değerler eski haline dönüyor mu?"

### ✅ Veri korunur:
- `docker compose stop` → container durur, **veri korunur**.
- `docker compose down` → container silinir, **veri korunur** (volume kalıcı).
- Backend / frontend rebuild → **veri korunur**.

### ❌ Veri silinir:
- `docker compose down -v` → ⚠️ **volume silinir, tüm DB sıfırlanır**.

### Seed neyi yazar?
Seed sadece **admin kullanıcısı yoksa** çalışır. Yani:
- İlk açılışta → 25 ürün, 18 sipariş, 15 kargo seed edilir.
- Sonraki açılışlarda → seed hiçbir şey yapmaz, mevcut verilerinizi korur.

**Sonuç:** Volume'u silmediğiniz sürece envanter değişiklikleriniz kalıcıdır.

---

## AI Görev Üretimi — Nasıl Çalışır?

> *"AI bu görevleri kafasına göre mi uyduruyor?"* — **Hayır.**

`POST /api/v1/tasks/generate` tetiklendiğinde `operations_agent.daily_briefing()`
şu üç gerçek veri kaynağını okur:

```
┌─────────────────────────────────────────────────────────┐
│           operations_agent.daily_briefing(db)           │
└─────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
 ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
 │ shipment_tool  │  │ inventory_tool │  │   task_tool    │
 │ Riskli/geciken │  │ Kritik stok    │  │ Açık görev    │
 │ kargolar       │  │ altındaki ürün │  │ kuyruğu       │
 └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
         ▼                   ▼                   ▼
   "Kargo X için        "Y ürünü için      "Görev: Z"
   müşteriye             tedarikçi
   bilgilendirme         siparişi
   gönder"               oluştur"
```

### Üretim Kuralları
1. **Geciken kargolar** → en riskli ilk 3 için: *"Kargo {tracking} için
   müşteriye bilgilendirme gönder."*
2. **Kritik stok** → eşik altındaki ilk 3 ürün için: *"{ürün} ({SKU})
   için tedarikçi siparişi oluştur."*
3. **Açık görevler** → mevcut kuyruktan ilk 3 tanesi listeye eklenir.

### Güvenlik İlkeleri
- ❌ Sahte sipariş veya SKU üretmez — sadece DB kayıtlarına referans.
- ✅ Her AI görev için "AI" rozeti UI'da görünür.
- ✅ Manuel görev de eklenebilir — `Görevler → Yeni Görev` butonu.

---

## AI Yaklaşımı

### Gemini Service (lazy + re-evaluable)
`gemini_service.py` tek seam. **Lazy init**: real backend ilk çağrıda kurulur;
`settings.use_real_gemini` her çağrıda yeniden okunur. Hata durumunda mock'a
otomatik düşer.

### RAG Pipeline
```
Belge → parse (pypdf/python-docx) → chunk (1200ch + 200 overlap)
     → embed (Gemini text-embedding-004 / hash-fallback)
     → persist (DocumentChunk.embedding_json)
     → retrieve (cosine sim, top-k=4)
     → context injection → Gemini grounded response
```

### Structured Outputs
```json
{
  "tracking_code": "KOP-RISK-000",
  "risk_level": "high",
  "risk_score": 0.78,
  "reason": "Kargo 52 saattir aynı transfer merkezinde bekliyor.",
  "recommended_action": "Müşteriye proaktif SMS gönder.",
  "confidence_score": 0.92
}
```

---

## API Referansı

Swagger: **`/docs`** · ReDoc: **`/redoc`**

| Grup | Endpoint | Açıklama |
| --- | --- | --- |
| Meta | `GET  /health/ai` 🆕 | AI backend canlı test |
| Auth | `POST /api/v1/auth/login` | JWT access + refresh |
| Chat | `POST /api/v1/chat/message` | RAG + agent |
| Docs | `POST /api/v1/documents/upload` | PDF/DOCX/TXT/CSV ingest |
| Inv. | `POST /api/v1/inventory/{id}/forecast` | AI tükenme tahmini |
| Ship | `POST /api/v1/shipments/{id}/check-status` | AI anomali analizi |
| Task | `POST /api/v1/tasks` | **Manuel** görev oluştur |
| Task | `POST /api/v1/tasks/generate` | **AI** günlük plan üret |
| Dash | `GET  /api/v1/dashboard/daily` | Yönetici brifingi |
| Portal | `GET  /api/v1/portal/my-orders` 🆕 | Müşterinin siparişleri |
| Portal | `GET  /api/v1/portal/my-shipments` 🆕 | Müşterinin kargoları |
| Portal | `GET  /api/v1/portal/track/{code}` 🆕 | Anonim takip |

---

## Klasör Yapısı

```
YZTA-Hackathon/
├── backend/
│   ├── app/
│   │   ├── ai/                   ← Gemini service, agent, RAG, tools, prompts
│   │   ├── api/v1/endpoints/     ← 10 router (portal dahil)
│   │   ├── core/                 ← security + RBAC
│   │   ├── models/               ← SQLAlchemy 2.0 ORM
│   │   ├── schemas/              ← Pydantic v2
│   │   ├── seed/seed_data.py     ← KoopAkıl demo verisi
│   │   └── main.py               ← /health, /health/ai
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── portal/               ← Müşteri paneli 🆕
│   │   │   ├── page.tsx          ← Siparişlerim
│   │   │   └── shipments/        ← Kargolarım
│   │   ├── dashboard, chat, inventory, shipments, tasks, …
│   ├── components/
│   │   ├── shell.tsx             ← Rol-bazlı sidebar
│   │   └── ui/                   ← Button, Card, Modal, Table, Badge
│   ├── lib/roles.ts              ← Rol haritası
│   ├── Dockerfile
│   └── package.json
├── infra/nginx.conf
├── docker-compose.yml
└── README.md
```

---

## Production Deployment

```bash
git clone <repo> /opt/koopakil
cd /opt/koopakil
cp .env.example .env
$EDITOR .env       # JWT_SECRET, POSTGRES_PASSWORD, GEMINI_API_KEY
docker compose up -d --build
docker compose logs -f backend
```

### Yedekleme
```bash
docker exec aegis-postgres pg_dump -U aegis aegis_kobi > backup-$(date +%F).sql
```

---

## Lisans

MIT © 2026 — KoopAkıl 🌿
