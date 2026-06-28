"""Supplementary client for the current TEFAS fund API (``/api/funds/*``).

TEFAS migrated (2026) to a Next.js SSR site backed by JSON endpoints under
``https://www.tefas.gov.tr/api/funds/``. This client is an **extra / fallback**
data source used to fill gaps the primary borsapy path leaves empty — notably
fund *portfolio allocation*, which borsapy no longer returns since the
migration. It never replaces the existing flow; on failure it degrades to a
structured ``{"ok": False, ...}`` envelope (the site sits behind bot
protection, so requests may be challenged/blocked/throttled).

Endpoints (request shapes captured verbatim from the live site, June 2026)::

    POST /api/funds/fonTurGetir          {"dil":"TR","flag":1}
        -> resultList: [{"sfonTuru":100,"sfonTurAciklama":"Borçlanma Araçları Şemsiye Fonu"}, ...]
    POST /api/funds/fonUnvanGetir        {"dil":"TR","tur":"YAT"}
        -> resultList: [{"tanim":"Hisse Senedi"}, ...]
    POST /api/funds/fonGnlBlgSiraliGetir {fonTipi, sfonTurKod, basTarih, bitTarih,
                                          basSira, bitSira, fonTurAciklama, ...}
        -> resultList: [ ...fund rows... ]   (paged via basSira/bitSira)
    POST /api/funds/dagilimSiraliGetirT  {... + sFonTurKod, fonKod, fonGrup, fonUnvanTip}
        -> resultList: [ ...portfolio distribution rows... ]

All responses share the envelope
``{"errorCode","errorMessage","resultList","toplamSayi","toplamSayfa"}``.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

TEFAS_BASE = "https://www.tefas.gov.tr"
TEFAS_PAGE = f"{TEFAS_BASE}/tr/fon-verileri"
API_BASE = f"{TEFAS_BASE}/api/funds"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Origin": TEFAS_BASE,
    "Referer": TEFAS_PAGE,
}


def _last_business_day(now: Optional[datetime] = None) -> datetime:
    """TEFAS publishes for past business days; step back over Sat/Sun."""
    d = now or datetime.now()
    while d.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        d -= timedelta(days=1)
    return d


def _to_yyyymmdd(value: Optional[str], default: str) -> str:
    """Accept 'YYYY-MM-DD' or 'YYYYMMDD'; fall back to default (YYYYMMDD)."""
    if not value:
        return default
    return value.replace("-", "")


class TefasApiProvider:
    """Best-effort direct client for the current TEFAS ``/api/funds/*`` endpoints.

    ``transport`` is injectable so tests can drive it with ``httpx.MockTransport``.
    """

    def __init__(self, timeout: float = 20.0, transport: Optional[httpx.BaseTransport] = None):
        self.timeout = timeout
        self._transport = transport

    # -- transport -----------------------------------------------------------
    def _post_sync(self, path: str, body: dict) -> dict:
        """Prime cookies via the page GET, then POST JSON; return normalized envelope."""
        try:
            with httpx.Client(
                timeout=self.timeout, follow_redirects=True, headers=_HEADERS,
                transport=self._transport,
            ) as client:
                # Best-effort WAF/cookie priming; ignore its outcome.
                try:
                    client.get(TEFAS_PAGE)
                except Exception:
                    pass
                resp = client.post(f"{API_BASE}/{path}", json=body)
                if resp.status_code == 429:
                    return {"ok": False, "error": "tefas_api_throttled",
                            "message": "TEFAS API throttling limit reached (HTTP 429).",
                            "status": 429}
                content_type = resp.headers.get("content-type", "")
                if resp.status_code >= 400 or "application/json" not in content_type:
                    return {"ok": False, "error": "tefas_api_unavailable",
                            "message": (f"TEFAS API returned HTTP {resp.status_code} / "
                                        f"'{content_type or 'no content-type'}' (likely bot protection)."),
                            "status": resp.status_code}
                data = resp.json()
        except Exception as exc:
            logger.debug("TEFAS API %s failed: %s", path, exc)
            return {"ok": False, "error": "tefas_api_fetch_failed", "message": str(exc)}

        if data.get("errorMessage"):
            return {"ok": False, "error": "tefas_api_error",
                    "message": data["errorMessage"], "raw": data}
        return {"ok": True, "result": data.get("resultList") or [],
                "total": data.get("toplamSayi"), "pages": data.get("toplamSayfa")}

    async def _post(self, path: str, body: dict) -> dict:
        return await asyncio.to_thread(self._post_sync, path, body)

    # -- lookup endpoints (known schemas) ------------------------------------
    async def fund_types(self, dil: str = "TR") -> dict:
        """Umbrella fund types -> [{'code': sfonTuru, 'name': sfonTurAciklama}]."""
        env = await self._post("fonTurGetir", {"dil": dil, "flag": 1})
        if env.get("ok"):
            env["types"] = [
                {"code": r.get("sfonTuru"), "name": r.get("sfonTurAciklama")}
                for r in env.get("result", []) if isinstance(r, dict)
            ]
        return env

    async def fund_categories(self, fund_type: str = "YAT", dil: str = "TR") -> dict:
        """Fund categories -> ['Hisse Senedi', 'Katılım', ...]."""
        env = await self._post("fonUnvanGetir", {"dil": dil, "tur": fund_type})
        if env.get("ok"):
            env["categories"] = [
                r.get("tanim") for r in env.get("result", [])
                if isinstance(r, dict) and r.get("tanim")
            ]
        return env

    # -- data endpoints (response rows passed through; schema not normalized) -
    def _base_body(self, fund_type, sfon_tur_kod, category, start, end, start_rank, end_rank):
        bd = _last_business_day().strftime("%Y%m%d")
        return {
            "fonTipi": fund_type, "fonKodu": None, "aramaMetni": None, "fonTurKod": None,
            "fonGrubu": None, "sfonTurKod": sfon_tur_kod,
            "basTarih": _to_yyyymmdd(start, bd), "bitTarih": _to_yyyymmdd(end, bd),
            "basSira": start_rank, "bitSira": end_rank, "fonTurAciklama": category,
            "dil": "TR", "kurucuKod": None,
        }

    async def fund_list(self, fund_type="YAT", sfon_tur_kod=None, category=None,
                        start=None, end=None, start_rank=1, end_rank=25) -> dict:
        """Paged fund list (fonGnlBlgSiraliGetir). resultList rows passed through raw."""
        body = self._base_body(fund_type, sfon_tur_kod, category, start, end, start_rank, end_rank)
        return await self._post("fonGnlBlgSiraliGetir", body)

    async def portfolio_distribution(self, fund_code=None, fund_type="YAT", sfon_tur_kod=None,
                                     category=None, start=None, end=None,
                                     start_rank=1, end_rank=25) -> dict:
        """Portfolio asset distribution (dagilimSiraliGetirT). Set fund_code for one fund."""
        body = self._base_body(fund_type, sfon_tur_kod, category, start, end, start_rank, end_rank)
        code = fund_code.upper() if fund_code else None
        body.update({"sFonTurKod": sfon_tur_kod, "fonKod": code, "fonGrup": "", "fonUnvanTip": ""})
        if code:
            body["fonKodu"] = code
        return await self._post("dagilimSiraliGetirT", body)


def map_distribution_rows(rows: list) -> list:
    """Best-effort map raw TEFAS distribution rows to {asset_type, weight, raw}.

    The populated dagilimSiraliGetirT schema was not captured live, so each row's
    raw dict is always preserved under ``raw``; asset_type/weight are heuristic
    (matched by Turkish key fragments) and may be None.
    """
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        asset_type = None
        weight = None
        for k, v in r.items():
            kl = str(k).lower()
            if asset_type is None and isinstance(v, str) and any(
                t in kl for t in ("tip", "tur", "kiymet", "varlik", "aciklama", "ad", "unvan")
            ):
                asset_type = v
            if weight is None and isinstance(v, (int, float)) and not isinstance(v, bool) and any(
                t in kl for t in ("oran", "yuzde", "pay", "agirlik", "dagilim")
            ):
                weight = v
        out.append({"asset_type": asset_type, "weight": weight, "raw": r})
    return out
