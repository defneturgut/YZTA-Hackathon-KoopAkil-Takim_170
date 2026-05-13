"""Application configuration via Pydantic Settings.

Loads environment variables once at process start. All other modules
import the single ``settings`` instance.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_logger = logging.getLogger("koopakil.config")


def _scan_env_files_for_key(name: str) -> str:
    """Last-ditch fallback: scan common .env locations for ``name``.

    Kullanıcı API key'i yanlışlıkla ``backend/.env`` veya başka bir yere
    koyduğunda da çalışsın diye eklendi. Sadece env var BOŞ ise tetiklenir
    — gerçek bir ortam değişkeni geldiyse ona dokunulmaz.
    """
    candidates = [
        Path("/app/.env"),                # container: backend build çıktısı
        Path("/app/backend/.env"),        # bind mount edilmiş repo
        Path("backend/.env"),             # geliştirici makinesi
        Path(".env.local"),
    ]
    for p in candidates:
        try:
            if not p.exists():
                continue
            for raw_line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith(f"{name}="):
                    value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if value:
                        _logger.info(
                            "config: %s ortam değişkeni boştu, %s dosyasından okundu.",
                            name,
                            p,
                        )
                        return value
        except Exception:  # noqa: BLE001
            continue
    return ""


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application -------------------------------------------------
    app_name: str = "KoopAkıl"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # ---- Server ------------------------------------------------------
    host: str = "0.0.0.0"
    port: int = 8000

    # ---- Security ----------------------------------------------------
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ---- Database ----------------------------------------------------
    database_url: str = "sqlite+aiosqlite:///./aegis_kobi.db"

    # ---- Redis -------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"

    # ---- AI / Gemini -------------------------------------------------
    ai_demo_mode: bool = True
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-pro"
    gemini_embed_model: str = "text-embedding-004"

    # ---- CORS --------------------------------------------------------
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ---- Seed --------------------------------------------------------
    seed_on_startup: bool = True

    @field_validator("ai_demo_mode", mode="before")
    @classmethod
    def _coerce_demo(cls, v):  # noqa: ANN001
        if isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes", "on"}
        return bool(v)

    @field_validator("gemini_api_key", mode="after")
    @classmethod
    def _maybe_load_from_file(cls, v: str) -> str:
        """If the env var is empty, try common .env file locations."""
        if v and v.strip():
            return v.strip()
        return _scan_env_files_for_key("GEMINI_API_KEY")

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def use_real_gemini(self) -> bool:
        """Use the real Gemini model whenever a valid-looking API key is set.

        We deliberately *ignore* ``ai_demo_mode`` when a key is present —
        users who provide a key expect the real model. To force mock mode
        with a key set, blank out ``GEMINI_API_KEY``.
        """
        key = (self.gemini_api_key or "").strip()
        return key.startswith("AIza") and len(key) > 20


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
