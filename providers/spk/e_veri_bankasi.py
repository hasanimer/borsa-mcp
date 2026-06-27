from __future__ import annotations

from urllib.parse import urljoin
from bs4 import BeautifulSoup
from domain.models import DataQualityMetadata, SpkDataSource, StructuredError
from domain.normalizers import clean_text
from .client import SPK_E_VERI_URL, SpkClient

KNOWN = ["Aracı Kuruluşlar","Bankalar","Halka Açık Şirketler","Payları Borsada İşlem Gören Şirketler","Payları Borsada İşlem Görmeyen Şirketler","Bağımsız Denetim Kuruluşları","Gayrimenkul Değerleme Şirketleri","Derecelendirme Kuruluşları","Borsa İstanbul","Takasbank","MKK","KAP","TEFAS","TSPB","SPL","GEFAS","YTM","TDUB"]

class SpkEVeriBankasiProvider:
    def __init__(self, client: SpkClient | None = None):
        self.client = client or SpkClient(cache_ttl=86400)

    def list_sources(self) -> dict:
        try:
            html, entry, warnings = self.client.get_text(SPK_E_VERI_URL)
        except Exception as exc:
            return StructuredError(error="spk_source_fetch_failed", message=str(exc), source="SPK e-Veri Bankası", source_url=SPK_E_VERI_URL, warnings=["SPK e-Veri Bankası could not be fetched."]).model_dump(mode="json")
        soup = BeautifulSoup(html, "html.parser")
        page_text = clean_text(soup.get_text(" "))
        meta = DataQualityMetadata(source="SPK e-Veri Bankası", source_url=SPK_E_VERI_URL, fetched_at=entry.fetched_at, confidence="high", warnings=["SPK e-Veri Bankası is treated as an official catalogue/source index, not a direct market-data API.", *warnings])
        rows: list[SpkDataSource] = []
        for a in soup.select("a[href]"):
            title = clean_text(a.get_text(" "))
            href = a.get("href")
            if not title:
                continue
            if any(k.lower() in title.lower() for k in KNOWN):
                rows.append(SpkDataSource(category=title, institution=title, title=title, url=urljoin(SPK_E_VERI_URL, href), metadata=meta))
        existing = {r.title.lower() for r in rows}
        for name in KNOWN:
            if name.lower() in page_text.lower() and name.lower() not in existing:
                rows.append(SpkDataSource(category=name, institution=name, title=name, url=None, metadata=meta))
        if not rows:
            return StructuredError(error="spk_source_parse_failed", message="No official data-source entries could be parsed from the SPK page.", source="SPK e-Veri Bankası", source_url=SPK_E_VERI_URL, warnings=meta.warnings).model_dump(mode="json")
        return {"data_sources": [r.model_dump(mode="json") for r in rows], "metadata": meta.model_dump(mode="json")}
