"""Gemini service abstraction.

Single seam between the rest of the app and Google Gemini. Production
deployments enable real calls by setting ``AI_DEMO_MODE=false`` and
providing ``GEMINI_API_KEY``. Demo mode produces deterministic,
realistic Turkish responses without touching the network — ideal for
hackathon demos, CI, and offline development.

Public surface:
    * GeminiService.generate(prompt, *, system, structured_schema, temperature)
    * GeminiService.embed(texts)
    * GeminiService.chat(messages, *, system, tools, structured_schema)

All methods are async. The mock backend mirrors the same signatures so
swap is zero-cost.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from app.config import settings

logger = logging.getLogger("aegis.ai.gemini")


# -------------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------------
@dataclass
class GeminiResponse:
    """Container for the result of a Gemini call."""

    text: str
    structured: Optional[Dict[str, Any]] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.85
    latency_ms: int = 0
    token_usage: int = 0
    model: str = "gemini-2.5-pro-mock"


# -------------------------------------------------------------------------
# Embedding helpers
# -------------------------------------------------------------------------
EMBED_DIM = 256


def _deterministic_embedding(text: str, dim: int = EMBED_DIM) -> List[float]:
    """Hash-based pseudo-embedding.

    Not a real semantic embedding, but stable and good enough for the
    demo's cosine-similarity retriever. The same text always produces
    the same vector across runs, so seeded KB content remains
    retrievable after a restart.
    """
    text = (text or "").strip().lower()
    if not text:
        return [0.0] * dim
    # Use multiple SHA-256 digests to fill the vector.
    raw = b""
    counter = 0
    while len(raw) < dim * 4:
        raw += hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest()
        counter += 1
    floats: List[float] = []
    for i in range(dim):
        chunk = raw[i * 4 : i * 4 + 4]
        # Map 4 bytes → signed float in [-1, 1].
        n = int.from_bytes(chunk, "big", signed=False)
        floats.append((n / 0xFFFFFFFF) * 2.0 - 1.0)
    # Normalise.
    norm = math.sqrt(sum(x * x for x in floats)) or 1.0
    return [x / norm for x in floats]


# -------------------------------------------------------------------------
# Helpers — extract tool-output from a synthesis prompt
# -------------------------------------------------------------------------
import re as _re


def _extract_tool_json(prompt: str, tool_name: str) -> Optional[Dict[str, Any]]:
    """Find a ``[tool_name] → {...}`` block in the synthesis prompt and parse it."""
    if not prompt:
        return None
    marker = f"[{tool_name}] →"
    idx = prompt.find(marker)
    if idx == -1:
        return None
    start = prompt.find("{", idx)
    if start == -1:
        return None
    # Brace-balanced scan to find the end of the JSON object.
    depth = 0
    in_str = False
    esc = False
    end = -1
    for i, ch in enumerate(prompt[start:], start=start):
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        return None
    try:
        return json.loads(prompt[start:end])
    except json.JSONDecodeError:
        return None


def _try_product_answer_from_prompt(prompt: str) -> Optional[str]:
    """If inventory_tool returned matches, craft a specific product answer."""
    data = _extract_tool_json(prompt, "inventory_tool")
    if not data:
        return None
    matches = data.get("matches") or []
    if not matches:
        return None
    if len(matches) == 1:
        m = matches[0]
        critical_note = (
            " Bu ürün kritik stok eşiğinin altında; en kısa zamanda tedarikçiye "
            "sipariş açılması önerilir."
            if m.get("is_low_stock")
            else ""
        )
        return (
            f"**{m.get('name')}** ({m.get('sku')}) ürününden şu anda "
            f"**{m.get('stock_qty')} {m.get('unit')}** kalmış. "
            f"Yeniden sipariş eşiği: {m.get('reorder_threshold')} {m.get('unit')}. "
            f"Tedarikçi: {m.get('supplier_name') or 'belirtilmemiş'}." + critical_note
        )
    # Birden fazla eşleşme
    lines = ["Sorgunuzla eşleşen birden fazla ürün buldum:"]
    for m in matches[:5]:
        lines.append(
            f"- **{m.get('name')}** ({m.get('sku')}): "
            f"{m.get('stock_qty')} {m.get('unit')} kalmış"
            + (" — kritik stok" if m.get("is_low_stock") else "")
        )
    lines.append("\nHangi ürün hakkında detay istediğinizi belirtirseniz daha açıklayıcı olabilirim.")
    return "\n".join(lines)


def _try_critical_inventory_answer(prompt: str) -> Optional[str]:
    """If the prompt asks about low stock and inventory_tool ran, list them."""
    data = _extract_tool_json(prompt, "inventory_tool")
    if not data:
        return None
    user_q = prompt.lower()
    asks_critical = any(
        k in user_q for k in ("azaldı", "azalan", "kritik", "tükendi", "yetiyor")
    )
    if not asks_critical:
        return None
    critical = data.get("critical_items") or []
    if not critical:
        return "Şu an stoğu eşik altına düşen ürün bulunmuyor. 🌿"
    lines = [f"Stoğu eşik altına düşen **{len(critical)} ürün** tespit ettim:"]
    for m in critical[:10]:
        lines.append(
            f"- **{m.get('name')}** ({m.get('sku')}): "
            f"kalan {m.get('stock_qty')} {m.get('unit')} — "
            f"eşik {m.get('reorder_threshold')} {m.get('unit')}"
        )
    lines.append("\nÖneri: tedarikçilere yenileme siparişi açılsın.")
    return "\n".join(lines)


# -------------------------------------------------------------------------
# Mock response synthesis (Turkish, business-realistic)
# -------------------------------------------------------------------------
class _MockGenerator:
    """Deterministic Turkish response synthesizer.

    Picks a response template based on keywords detected in the prompt.
    Designed to look like a competent senior support agent + operations
    analyst — never invents fake order numbers; if the prompt does not
    mention one, the response phrases everything abstractly.
    """

    def __init__(self) -> None:
        self._rng = random.Random(42)

    def generate_text(self, prompt: str, system: str = "") -> str:
        text = (prompt or "").lower()
        full = (system + " " + prompt).lower()

        # ---- Tool-output aware mock answers ---------------------------
        # call_with_tools() bizim mock'a synthesis_prompt geçtiğinde tool
        # JSON çıktılarını da içerir. Bunu parse edip *gerçek* DB verisine
        # dayalı bir yanıt üretiriz — mock olsa bile UI doğru sayıyı gösterir.
        product_answer = _try_product_answer_from_prompt(prompt)
        if product_answer:
            return product_answer
        critical_answer = _try_critical_inventory_answer(prompt)
        if critical_answer:
            return critical_answer

        # ---- Customer support intents ---------------------------------
        if any(k in text for k in ["siparişim nerede", "kargom nerede", "siparişim ne zaman", "kargo durumu"]):
            return (
                "Siparişinizi sistemde sorguladım. Şu anda kargo işlemleri devam ediyor; "
                "tedarikçi onayının ardından paketiniz dağıtım merkezine aktarıldı ve "
                "tahmini teslim süresi 1-2 iş günüdür. Kargo takip kodunuz hesabınızdaki "
                "“Kargolarım” sekmesinden de görüntülenebilir. Gecikme tespit edersek size "
                "otomatik bildirim göndereceğiz."
            )
        if "iade" in text:
            return (
                "İade sürecimiz şu adımlardan oluşur: (1) hesabınızdan iade talebi oluşturun, "
                "(2) sistem size kargo etiketi e-postalar, (3) ürünü orijinal ambalajıyla "
                "anlaşmalı kargoya teslim edin, (4) ürün depomuza ulaştıktan sonra 3 iş günü "
                "içinde iade onayı ve ödeme iadesi tamamlanır. Mevzuat gereği iade süresi "
                "teslim tarihinden itibaren 14 gündür."
            )
        if "stok" in text or "mevcut" in text:
            return (
                "Stok bilgisini gerçek zamanlı olarak kontrol ettim. İlgili ürün şu anda "
                "envanterimizde mevcut; ancak tedarikçi planına bağlı olarak kritik eşik "
                "yaklaştığında otomatik yenileme talebi tetiklenir. Sipariş vermek isterseniz "
                "doğrudan ürün sayfasından devam edebilirsiniz."
            )
        if "çalışma saat" in text or "saat kaçta" in text:
            return (
                "Müşteri destek hattımız hafta içi 09:00 – 18:00 arasında çalışmaktadır. "
                "Bu kanal üzerinden 7/24 AI asistanımıza ulaşabilir, siparişlerinizi ve "
                "kargolarınızı sorgulayabilirsiniz."
            )

        # ---- Logistics / risk analysis --------------------------------
        if any(k in full for k in ["gecikme", "risk", "anomali", "shipment"]):
            return (
                "Lojistik analiz tamamlandı. Son 72 saatte aynı transit merkezinde bekleyen "
                "kargolar tespit edildi; risk skoru orta-yüksek olarak işaretlendi. Önerilen "
                "aksiyon: ilgili müşterilere proaktif bilgilendirme gönderilmesi ve carrier "
                "ile entegrasyon API'sinin yenilenmesidir."
            )

        # ---- Inventory prediction ------------------------------------
        if any(k in full for k in ["tahmin", "öngörü", "envanter", "sipariş ver", "tedarikçi"]):
            return (
                "Geçmiş 30 günlük satış verisi analiz edildi. Trend, haftalık ortalama satışın "
                "yaklaşık %12 üzerinde seyrediyor. Mevcut stoğun ilgili ürün için 4-6 gün "
                "içinde kritik eşiğin altına düşmesi bekleniyor. Tedarikçiye en geç önümüzdeki "
                "Salı günü sipariş açılması önerilir."
            )

        # ---- Daily ops planning --------------------------------------
        if any(k in full for k in ["günlük plan", "operasyon", "rotalama", "depo görev"]):
            return (
                "Bugünün operasyon planı hazırlandı. Depo ekibi için 12 paket öncelikli, 7 "
                "paket normal sırada listelendi. Kurye için en kısa rota İstanbul/Kadıköy → "
                "Üsküdar → Beşiktaş şeklinde optimize edildi. Yönetici özetinde 2 kritik stok "
                "uyarısı ve 1 gecikme riski yer alıyor."
            )

        # ---- Default fallback ----------------------------------------
        return (
            "Bu konuda elimde kesin bir bilgi yok. Daha fazla bağlam sağlarsanız "
            "(sipariş numarası, ürün adı, tarih aralığı vb.) daha doğru bir yanıt "
            "üretebilirim."
        )

    def generate_structured(self, prompt: str, schema_hint: Dict[str, Any]) -> Dict[str, Any]:
        """Return mock JSON consistent with the schema hint."""
        text = (prompt or "").lower()
        if "risk" in text or "gecikme" in text or "shipment" in text:
            return {
                "risk_level": "high",
                "risk_score": 0.78,
                "reason": "Kargo 48 saatten fazla aynı transfer merkezinde beklemekte.",
                "recommended_action": "Müşteriyi proaktif bilgilendir ve carrier ile vakayı aç.",
                "confidence_score": 0.92,
            }
        if "stok" in text or "tahmin" in text:
            return {
                "predicted_days_to_stockout": 5,
                "recommended_reorder_qty": 80,
                "trend": "artan",
                "confidence_score": 0.87,
                "reason": "Son 14 günde günlük ortalama satış %15 arttı.",
            }
        # Generic structured fallback.
        return {"status": "ok", "confidence_score": 0.8}


# -------------------------------------------------------------------------
# Real Gemini backend (lazy-loaded)
# -------------------------------------------------------------------------
class _RealGeminiBackend:
    """Async wrapper around google-generativeai.

    The system prompt is bound to the model at construction time so every
    generate() call inherits Aegis-KOBİ's tone and safety rules. Embedding
    calls fall back to the mock embedder on quota/network errors so a hot
    Gemini outage never takes the whole app down.
    """

    def __init__(self) -> None:
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "google-generativeai not installed but real Gemini mode enabled."
            ) from e
        genai.configure(api_key=settings.gemini_api_key)
        self._genai = genai
        self._default_system = (
            "Sen Aegis-KOBİ platformunun yapay zeka asistanısın. "
            "Her zaman Türkçe yanıt ver, kurumsal ve sıcak bir ton kullan, "
            "bilmediğin şeyi 'Bu bilgiye erişemiyorum' diyerek söyle, "
            "asla veri uydurma."
        )

    def _model_for(self, system: str):
        """Build a per-call model so the system prompt can be customised."""
        return self._genai.GenerativeModel(
            settings.gemini_model,
            system_instruction=system or self._default_system,
        )

    async def generate(
        self,
        prompt: str,
        system: str,
        temperature: float,
        structured: bool = False,
    ) -> str:
        loop = asyncio.get_running_loop()

        def _run() -> str:
            model = self._model_for(system)
            generation_config: Dict[str, Any] = {
                "temperature": float(temperature),
                "max_output_tokens": 2048,
                "top_p": 0.9,
            }
            if structured:
                # Ask Gemini to return valid JSON when a structured schema is set.
                generation_config["response_mime_type"] = "application/json"
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    # 25s — hızlı geri-bildirim, kullanıcıyı bekletmeden mock'a düşeriz
                    request_options={"timeout": 25},
                )
                return (getattr(response, "text", "") or "").strip()
            except Exception as e:  # noqa: BLE001
                logger.warning("Gemini generate failed: %s", e)
                return ""

        # Outer asyncio timeout — even if the SDK ignores request_options,
        # asyncio guarantees we never wait more than 30s for a single call.
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, _run), timeout=30
            )
        except asyncio.TimeoutError:
            logger.warning("Gemini generate timeout (>30s) — returning empty.")
            return ""

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        loop = asyncio.get_running_loop()

        def _run() -> List[List[float]]:
            out: List[List[float]] = []
            for t in texts:
                try:
                    resp = self._genai.embed_content(
                        model=settings.gemini_embed_model,
                        content=t,
                        task_type="retrieval_document",
                    )
                    out.append(list(resp["embedding"]))
                except Exception as e:  # noqa: BLE001
                    logger.warning(
                        "Gemini embed failed for one chunk (%s) — using fallback.", e
                    )
                    out.append(_deterministic_embedding(t))
            return out

        return await loop.run_in_executor(None, _run)


# -------------------------------------------------------------------------
# Public service
# -------------------------------------------------------------------------
class GeminiService:
    """Unified async interface for Gemini-powered AI features.

    The real backend is *lazy-initialised* on first use so adding an API
    key to `.env` and restarting the backend is the only step required —
    no code change. Each call re-reads ``settings.use_real_gemini``, so if
    the key becomes invalid or is removed at runtime, we transparently
    fall back to mock without crashing.
    """

    def __init__(self) -> None:
        self._mock = _MockGenerator()
        self._real: Optional[_RealGeminiBackend] = None
        self._last_status: Dict[str, Any] = {
            "backend": "mock",
            "model": "mock",
            "last_check": None,
            "last_error": None,
        }

    # Public read-only status surface used by /health/ai.
    @property
    def status(self) -> Dict[str, Any]:
        return dict(self._last_status)

    @property
    def _use_real(self) -> bool:
        """Re-evaluate on every call so .env edits + restart are enough."""
        return settings.use_real_gemini

    def _get_real(self) -> Optional["_RealGeminiBackend"]:
        """Lazy-build the real backend; cache for the process lifetime."""
        if not self._use_real:
            return None
        if self._real is None:
            try:
                self._real = _RealGeminiBackend()
                logger.info(
                    "GeminiService: real backend ready (model=%s).",
                    settings.gemini_model,
                )
            except Exception as e:  # pragma: no cover
                logger.error("Could not initialise real Gemini backend: %s", e)
                self._last_status["last_error"] = str(e)
                return None
        return self._real

    # ----- text generation ------------------------------------------------
    async def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0.4,
        structured_schema: Optional[Dict[str, Any]] = None,
    ) -> GeminiResponse:
        start = time.perf_counter()
        real = self._get_real()
        if real is not None:
            text = await real.generate(
                prompt,
                system,
                temperature,
                structured=bool(structured_schema),
            )
            structured = None
            if structured_schema:
                try:
                    structured = json.loads(text) if text else None
                except json.JSONDecodeError:
                    structured = self._mock.generate_structured(prompt, structured_schema)
            # Empty real response → fall back to mock so demos don't break.
            if not text:
                self._last_status["last_error"] = "Gemini returned empty response"
                text = self._mock.generate_text(prompt, system)
                self._last_status["backend"] = "mock-fallback"
            else:
                self._last_status["backend"] = "gemini"
                self._last_status["model"] = settings.gemini_model
                self._last_status["last_error"] = None
        else:
            # Tiny artificial latency so the demo feels real on the UI.
            await asyncio.sleep(0.15)
            text = self._mock.generate_text(prompt, system)
            structured = (
                self._mock.generate_structured(prompt, structured_schema)
                if structured_schema
                else None
            )

        latency_ms = int((time.perf_counter() - start) * 1000)
        # Confidence: structured output → higher; long prose → slightly lower.
        confidence = 0.92 if structured else max(0.65, min(0.95, 1.0 - len(text) / 4000))
        in_real_mode = real is not None and self._last_status["backend"] == "gemini"
        model_label = (
            settings.gemini_model
            if in_real_mode
            else f"{settings.gemini_model}-mock"
        )
        return GeminiResponse(
            text=text,
            structured=structured,
            confidence=round(confidence, 2),
            latency_ms=latency_ms,
            token_usage=max(1, len(text.split())),
            model=model_label,
        )

    # ----- chat-style (multi-turn) ----------------------------------------
    async def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        system: str = "",
        structured_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.4,
    ) -> GeminiResponse:
        """Flattens a multi-turn history into a single prompt and delegates."""
        history = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)
        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            "",
        )
        prompt = f"{history}\n\nLütfen son kullanıcı mesajına Türkçe yanıt ver."
        resp = await self.generate(
            prompt,
            system=system,
            temperature=temperature,
            structured_schema=structured_schema,
        )
        # Replace the response text with one tailored to the last user turn
        # for a more natural demo (history pre-context still influences mock).
        if not self._use_real:
            resp.text = self._mock.generate_text(last_user, system)
        return resp

    # ----- embeddings -----------------------------------------------------
    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        real = self._get_real()
        if real is not None:
            return await real.embed(texts)
        await asyncio.sleep(0.01 * len(texts))
        return [_deterministic_embedding(t) for t in texts]

    # ----- health probe (used by /api/v1/health/ai) -----------------------
    async def health_check(self) -> Dict[str, Any]:
        """Ping the active backend and return a status payload."""
        real = self._get_real()
        backend = "gemini" if real else "mock"
        info: Dict[str, Any] = {
            "backend": backend,
            "model": settings.gemini_model if backend == "gemini" else "mock",
            "demo_mode_flag": settings.ai_demo_mode,
            "key_configured": bool(settings.gemini_api_key),
            "key_looks_valid": settings.use_real_gemini,
        }
        try:
            r = await self.generate(
                "Lütfen sadece 'KoopAkıl AI hazır.' yaz.",
                temperature=0.0,
            )
            info["sample_response"] = r.text[:120]
            info["latency_ms"] = r.latency_ms
            info["ok"] = True
            info["last_error"] = self._last_status.get("last_error")
        except Exception as e:  # noqa: BLE001
            info["ok"] = False
            info["last_error"] = str(e)
        return info

    # ----- function / tool calling ---------------------------------------
    async def call_with_tools(
        self,
        prompt: str,
        tools: Dict[str, Callable[..., Any]],
        *,
        system: str = "",
        max_steps: int = 3,
    ) -> GeminiResponse:
        """Naive reasoning loop used by ``OperationsAgent``.

        Mock implementation routes by keyword to the matching tool. The
        real implementation would use Gemini's native function calling,
        but the contract is identical — the agent code stays the same.
        """
        chosen: List[Dict[str, Any]] = []
        lower = prompt.lower()
        tool_results: List[str] = []

        async def _maybe_run(name: str, **kwargs: Any) -> None:
            fn = tools.get(name)
            if not fn:
                return
            try:
                result = await fn(**kwargs) if asyncio.iscoroutinefunction(fn) else fn(**kwargs)
            except Exception as e:  # noqa: BLE001
                result = {"error": str(e)}
            chosen.append({"tool": name, "arguments": kwargs, "result": result})
            # Tool çıktısı için cömert bir bütçe — gerçek Gemini'nin
            # synthesis için tüm ürün/kargo listesini görmesi gerekir.
            tool_results.append(
                f"[{name}] → {json.dumps(result, default=str, ensure_ascii=False)[:4000]}"
            )

        # ----- Inventory ---------------------------------------------------
        # Çok geniş kelime listesi: "Defne sabunundan kaç tane kaldı?",
        # "Bal mevcut mu?", "Çay var mı?" gibi sorgular da yakalanır.
        inventory_keywords = (
            "stok", "envanter", "kritik", "azalan", "azaldı",
            "kalan", "kaldı", "kala", "mevcut", "ürün",
            "kaç", "ne kadar", "adet", "var mı", "tükendi",
            "tedarik", "yenile", "sipariş ver",
        )
        # Ek olarak: yaygın ürün isimlerinden biri geçiyorsa da inventory çek.
        product_hints = (
            "sabun", "zeytinyağı", "bal", "peynir", "kahve", "çay",
            "yumurta", "un", "bulgur", "mercimek", "fasulye", "fındık",
            "ceviz", "badem", "reçel", "şekerleme", "yastık", "sofra bezi",
            "kupa", "salça", "bahar çay",
        )
        if any(k in lower for k in inventory_keywords + product_hints):
            # Kullanıcı sorgusunu inventory_tool'a geçir ki spesifik ürün
            # eşleşmeleri `matches` alanında öne çıksın.
            await _maybe_run("inventory_tool", query=prompt)

        # ----- Shipment ---------------------------------------------------
        if any(
            k in lower
            for k in (
                "kargo", "shipment", "geciken", "gecikme", "teslim",
                "yolda", "gönderi", "takip", "transit",
            )
        ):
            await _maybe_run("shipment_tool")

        # ----- Analytics --------------------------------------------------
        if any(
            k in lower
            for k in ("risk", "analiz", "satış", "rapor", "trend", "kpı", "kpi")
        ):
            await _maybe_run("analytics_tool")

        # ----- Tasks ------------------------------------------------------
        if any(
            k in lower
            for k in ("görev", "plan", "rota", "operasyon", "iş listesi")
        ):
            await _maybe_run("task_tool")

        # If nothing matched, run analytics + inventory as a default.
        if not chosen:
            await _maybe_run("inventory_tool")
            await _maybe_run("analytics_tool")

        synthesis_prompt = (
            f"{system}\n\nKullanıcı isteği: {prompt}\n\n"
            f"Tool çıktıları:\n" + "\n".join(tool_results)
            + "\n\nBu verilere dayanarak, kurumsal Türkçe, kaynak gösteren özet bir cevap üret."
        )
        resp = await self.generate(synthesis_prompt, system=system, temperature=0.3)
        resp.tool_calls = chosen
        return resp


# Singleton — imported by routers, agents, RAG.
gemini_service = GeminiService()
