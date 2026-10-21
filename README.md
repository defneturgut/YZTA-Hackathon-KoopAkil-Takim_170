# 🌿 KoopAkıl — Your Cooperative's Smart Assistant

> An end-to-end, **Gemini AI-powered** operations platform for producer
> cooperatives and SMEs. It brings customer support, shipping logistics,
> smart inventory management and daily operations planning together in a
> single, simple interface.

[![Python](https://img.shields.io/badge/python-3.12-3776AB?style=flat-square)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square)](https://nextjs.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Pro-4285F4?style=flat-square)](https://ai.google.dev/)

---

## Table of Contents

1. [At a Glance](#at-a-glance)
2. [Target Users & Design Philosophy](#target-users--design-philosophy)
3. [Role-Based Experience](#role-based-experience)
4. [Architecture](#architecture)
5. [Modules](#modules)
6. [Quick Start](#quick-start)
7. [⚙️ Switching to the Real Gemini API & Troubleshooting](#️-switching-to-the-real-gemini-api--troubleshooting)
8. [💾 Data Persistence](#-data-persistence)
9. [AI Task Generation — How Does It Work?](#ai-task-generation--how-does-it-work)
10. [AI Approach](#ai-approach)
11. [API Reference](#api-reference)
12. [Folder Structure](#folder-structure)
13. [Production Deployment](#production-deployment)

---

## At a Glance

| Aspect | Detail |
| --- | --- |
| **Project** | KoopAkıl |
| **Target Audience** | Agricultural/handicraft cooperatives, small e-commerce |
| **Core Capability** | Multi-tool AI agent + RAG + anomaly detection + daily briefing + manual + AI task generation + customer portal |
| **Stack** | FastAPI · SQLAlchemy 2.0 · Next.js 15 · Tailwind · Recharts |
| **AI** | Google **Gemini 2.5 Pro** + Embeddings + Function Calling |
| **Design** | Light theme · natural green/cream palette · clean typography |
| **Modes** | Demo (mock, no key needed) · Production (with a real Gemini key) |

---

## Target Users & Design Philosophy

KoopAkıl targets **agricultural cooperatives and boutique producers with
20–200 products**. Most of their staff are non-technical — so:

- 🤍 **White background + soft green/cream** — easy on the eyes, feels natural
- 🌿 **Large typography, generous spacing, icon-backed buttons**
- 🇹🇷 **Entire UI in Turkish** — everyday language instead of technical jargon
- 🪜 **Role-based simplicity** — a warehouse worker never sees the management panel
- 💚 **Helpful messages** — "Packages to prepare today", "Products running low"

---

## Role-Based Experience

Each user role opens on a screen suited to it. The sidebar is filtered automatically.

| Role | After Login | Sidebar Contents |
| --- | --- | --- |
| **Manager / Admin** | `/dashboard` | Everything |
| **Warehouse Staff** | `/tasks` ("Packages to prepare today") | Home · Inventory · Tasks · Alerts · Settings |
| **Courier** | `/shipments` ("Your route today") | Home · Shipments · Tasks · Settings |
| **Customer Support** | `/chat` (AI Assistant) | Home · AI Assistant · Shipments · Alerts · Settings |
| **Customer** 🆕 | `/portal` (My Orders) | My Orders · My Shipments · Settings |

> A user with the customer role sees **only their own** orders and
> shipments — the backend filters by `Order.customer_email`. They have no
> access to management screens.

---

## Architecture

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

## Modules

### Module 1 — AI Customer Support Center
- Web chat, multi-turn Turkish, Redis-based session memory
- **RAG**: PDF/DOCX/TXT/CSV upload → chunking → Gemini embeddings → cosine retrieval → grounded response
- Source citations + confidence score + hallucination reduction

### Module 2 — Shipping & Logistics AI
- Shipment tracking + event log
- **AI anomaly detection**: 48+ hour stalls, transit delays, high-risk deliveries

### Module 3 — Smart Inventory Management
- Low-stock detection + live KPIs
- AI predictive forecast: stock-out date + recommended order quantity

### Module 4 — Daily Operations Agent
- **Multi-tool agent**: 4 tools + Gemini reasoning + structured outputs
- **Manual + AI task generation**

### Module 5 — Customer Portal 🆕
- Customers see their own orders and shipments
- Shipment timeline (every event/status step)

---

## Quick Start

### One command with Docker

```bash
git clone https://github.com/defneturgut/YZTA-Hackathon-KoopAkil-Takim_170.git
cd YZTA-Hackathon-KoopAkil-Takim_170
cp .env.example .env
docker compose up --build
```

Then:
- 🌐 Frontend: <http://localhost:3000>
- ⚙️ Backend Swagger: <http://localhost:8000/docs>
- 🩺 AI health check: <http://localhost:8000/health/ai>

### Demo Accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@koopakil.tr` | `admin1234` |
| Manager | `yonetici@koopakil.tr` | `admin1234` |
| Warehouse | `depo@koopakil.tr` | `admin1234` |
| Courier | `kurye@koopakil.tr` | `admin1234` |
| Support | `destek@koopakil.tr` | `admin1234` |
| **Customer** | `musteri@koopakil.tr` | `admin1234` |

> The first 5 orders are assigned to the demo customer `Zeynep Aydın` during
> seeding, so the customer portal shows a populated history.

---

## ⚙️ Switching to the Real Gemini API & Troubleshooting

### One rule: **if there is an API key, real Gemini is used.**

Add a valid key to your `.env` file and restart the backend:

```env
GEMINI_API_KEY=AIzaSy....   # get one for free at https://ai.google.dev
GEMINI_MODEL=gemini-2.5-pro
```

```bash
docker compose restart backend
```

You should see this line in the backend log:
```
✅ AI backend: REAL Gemini (model=gemini-2.5-pro) — key configured
```

### 🐛 "I added an API key but the AI still gives mock responses"

1. **Wrong key format** → a valid key starts with `AIza` and is > 20 characters
   ```bash
   docker compose exec backend env | grep GEMINI_API_KEY
   ```

2. **Backend not restarted** → `.env` changes only take effect after a
   restart:
   ```bash
   docker compose restart backend
   ```

3. **Test AI health** → comprehensive debug endpoint:
   ```bash
   curl http://localhost:8000/health/ai
   ```
   When it works:
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
   If something is wrong, the `last_error` field tells you what.

4. **Quota / billing** → Gemini's free tier is 60 RPM. If it is exceeded,
   the system **automatically falls back to mock** (so the app doesn't crash).

### Force mock mode
To fall back to mock even with a key, set `GEMINI_API_KEY=` (empty) in `.env`.

---

## 💾 Data Persistence

> "Will the values I changed in inventory reset?"

### ✅ Data is kept:
- `docker compose stop` → the container stops, **data is kept**.
- `docker compose down` → the container is removed, **data is kept** (the volume persists).
- Backend / frontend rebuild → **data is kept**.

### ❌ Data is deleted:
- `docker compose down -v` → ⚠️ **the volume is deleted and the whole DB is reset**.

### What does the seed write?
The seed only runs **if there is no admin user**. So:
- On first start → 25 products, 18 orders and 15 shipments are seeded.
- On later starts → the seed does nothing and keeps your existing data.

**Result:** as long as you don't delete the volume, your inventory changes persist.

---

## AI Task Generation — How Does It Work?

> *"Does the AI just make these tasks up?"* — **No.**

When `POST /api/v1/tasks/generate` is triggered, `operations_agent.daily_briefing()`
reads these three real data sources:

```
┌─────────────────────────────────────────────────────────┐
│           operations_agent.daily_briefing(db)           │
└─────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
 ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
 │ shipment_tool  │  │ inventory_tool │  │   task_tool    │
 │ Risky/delayed  │  │ Products below │  │ Open task      │
 │ shipments      │  │ critical stock │  │ queue          │
 └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
         ▼                   ▼                   ▼
   "Send the            "Create a           "Task: Z"
   customer an          supplier order
   update for           for product Y"
   shipment X"
```

### Generation Rules
1. **Delayed shipments** → for the 3 riskiest: *"Send the customer an update
   for shipment {tracking}."*
2. **Critical stock** → for the first 3 products below the threshold: *"Create
   a supplier order for {product} ({SKU})."*
3. **Open tasks** → the first 3 from the existing queue are added to the list.

### Safety Principles
- ❌ Never invents orders or SKUs — only references DB records.
- ✅ Every AI-generated task shows an "AI" badge in the UI.
- ✅ Manual tasks can also be added — via the `Tasks → New Task` button.

---

## AI Approach

### Gemini Service (lazy + re-evaluable)
`gemini_service.py` is the single seam. **Lazy init**: the real backend is set up on the
first call; `settings.use_real_gemini` is re-read on every call. On errors it
automatically falls back to mock.

### RAG Pipeline
```
Document → parse (pypdf/python-docx) → chunk (1200ch + 200 overlap)
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
  "reason": "The shipment has been waiting at the same transfer hub for 52 hours.",
  "recommended_action": "Send the customer a proactive SMS.",
  "confidence_score": 0.92
}
```

---

## API Reference

Swagger: **`/docs`** · ReDoc: **`/redoc`**

| Group | Endpoint | Description |
| --- | --- | --- |
| Meta | `GET  /health/ai` 🆕 | Live AI backend test |
| Auth | `POST /api/v1/auth/login` | JWT access + refresh |
| Chat | `POST /api/v1/chat/message` | RAG + agent |
| Docs | `POST /api/v1/documents/upload` | PDF/DOCX/TXT/CSV ingest |
| Inv. | `POST /api/v1/inventory/{id}/forecast` | AI stock-out forecast |
| Ship | `POST /api/v1/shipments/{id}/check-status` | AI anomaly analysis |
| Task | `POST /api/v1/tasks` | Create a **manual** task |
| Task | `POST /api/v1/tasks/generate` | Generate an **AI** daily plan |
| Dash | `GET  /api/v1/dashboard/daily` | Manager briefing |
| Portal | `GET  /api/v1/portal/my-orders` 🆕 | Customer's orders |
| Portal | `GET  /api/v1/portal/my-shipments` 🆕 | Customer's shipments |
| Portal | `GET  /api/v1/portal/track/{code}` 🆕 | Anonymous tracking |

---

## Folder Structure

```
YZTA-Hackathon/
├── backend/
│   ├── app/
│   │   ├── ai/                   ← Gemini service, agent, RAG, tools, prompts
│   │   ├── api/v1/endpoints/     ← 10 routers (including portal)
│   │   ├── core/                 ← security + RBAC
│   │   ├── models/               ← SQLAlchemy 2.0 ORM
│   │   ├── schemas/              ← Pydantic v2
│   │   ├── seed/seed_data.py     ← KoopAkıl demo data
│   │   └── main.py               ← /health, /health/ai
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── portal/               ← Customer portal 🆕
│   │   │   ├── page.tsx          ← My Orders
│   │   │   └── shipments/        ← My Shipments
│   │   ├── dashboard, chat, inventory, shipments, tasks, …
│   ├── components/
│   │   ├── shell.tsx             ← Role-based sidebar
│   │   └── ui/                   ← Button, Card, Modal, Table, Badge
│   ├── lib/roles.ts              ← Role map
│   ├── Dockerfile
│   └── package.json
├── infra/nginx.conf
├── docker-compose.yml
└── README.md
```

---

## Production Deployment

```bash
git clone https://github.com/defneturgut/YZTA-Hackathon-KoopAkil-Takim_170.git /opt/koopakil
cd /opt/koopakil
cp .env.example .env
$EDITOR .env       # JWT_SECRET, POSTGRES_PASSWORD, GEMINI_API_KEY
docker compose up -d --build
docker compose logs -f backend
```

### Backup
```bash
docker exec aegis-postgres pg_dump -U aegis aegis_kobi > backup-$(date +%F).sql
```

---

## License

MIT © 2026 — KoopAkıl 🌿
