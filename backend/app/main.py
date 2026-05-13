"""FastAPI application entry point.

Wires CORS, logging, the v1 API router, startup hooks (DB init +
optional seed) and friendly health-check routes for the app, DB and
the AI backend.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.ai.services.gemini_service import gemini_service
from app.api.v1.api import api_router
from app.config import settings
from app.database import init_db

# ---------------------------------------------------------------------
# Logging — single-line JSON-ish format for production grep-ability.
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO if not settings.app_debug else logging.DEBUG,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("koopakil.main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "Starting %s v%s in %s mode", settings.app_name, __version__, settings.app_env
    )
    await init_db()
    logger.info("Database schema ensured.")

    if settings.seed_on_startup:
        # Local import keeps startup quick when seeding is disabled.
        from app.seed.seed_data import seed_database

        await seed_database()
        logger.info("Seed data ensured.")

    # ----- AI backend status banner ----------------------------------
    raw_key = (settings.gemini_api_key or "").strip()
    if raw_key:
        # Preview yalnızca ilk/son birkaç karakter; tam key log'a yazılmaz.
        if len(raw_key) > 14:
            preview = f"{raw_key[:8]}…{raw_key[-4:]}"
        else:
            preview = "(çok kısa)"
        logger.info(
            "🔑 GEMINI_API_KEY = %s (uzunluk=%d, başlangıç-doğru=%s)",
            preview,
            len(raw_key),
            raw_key.startswith("AIza"),
        )
    else:
        logger.warning(
            "🔑 GEMINI_API_KEY = (BOŞ)  →  Backend hiç key görmüyor. "
            "Root .env dosyasını kontrol edin (backend/.env değil)."
        )

    if settings.use_real_gemini:
        logger.info(
            "✅ AI backend: REAL Gemini (model=%s)", settings.gemini_model
        )
        # Self-test — sadece startup'ta bir kez, hızlı bir prompt
        try:
            probe = await gemini_service.health_check()
            if probe.get("ok"):
                logger.info(
                    "✅ Gemini self-test başarılı (latency=%sms): %s",
                    probe.get("latency_ms"),
                    (probe.get("sample_response") or "")[:80],
                )
            else:
                logger.error(
                    "❌ Gemini self-test BAŞARISIZ: %s — mock fallback kullanılacak",
                    probe.get("last_error"),
                )
        except Exception as e:  # noqa: BLE001
            logger.error("❌ Gemini self-test exception: %s", e)
    elif raw_key:
        logger.warning(
            "⚠️  AI backend: MOCK — GEMINI_API_KEY var ama 'AIza' ile "
            "başlamıyor veya kısa. Doğru key formatını kontrol edin."
        )
    else:
        logger.info(
            "🧪 AI backend: MOCK — GEMINI_API_KEY yok. Demo modunda çalışıyor."
        )

    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=f"{settings.app_name} API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    description=(
        "KoopAkıl — Üretici kooperatifleri ve KOBİ'ler için yapay zeka destekli "
        "operasyon ve lojistik merkezi. Müşteri destek, kargo lojistiği, "
        "akıllı stok yönetimi ve günlük operasyon ajanını tek API altında "
        "birleştirir."
    ),
)

# CORS — frontend dev origin needs to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": __version__,
        "status": "ok",
        "docs": "/docs",
        "api": settings.api_v1_prefix,
        "ai_backend": "gemini" if settings.use_real_gemini else "mock",
    }


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "healthy", "app": settings.app_name}


@app.get("/health/ai", tags=["meta"])
async def health_ai() -> dict:
    """Live-probe the AI backend. Useful for verifying the API key works."""
    return await gemini_service.health_check()


app.include_router(api_router, prefix=settings.api_v1_prefix)
