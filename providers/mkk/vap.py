from __future__ import annotations
import re
from bs4 import BeautifulSoup
from domain.normalizers import clean_text, parse_number
from domain.models import DataQualityMetadata, StructuredError
from .client import MKK_VAP_URL, MkkClient

class MkkVapProvider:
    def __init__(self, client: MkkClient | None = None): self.client = client or MkkClient(cache_ttl=3600)
    def fetch_page(self): return self.client.get_text(MKK_VAP_URL)
    def market_summary(self) -> dict:
        try: html, entry, warnings = self.fetch_page()
        except Exception as exc: return StructuredError(error="mkk_vap_fetch_failed", message=str(exc), source="MKK / VAP", source_url=MKK_VAP_URL, warnings=["MKK/VAP source could not be fetched."]).model_dump(mode="json")
        soup = BeautifulSoup(html, "html.parser"); text = clean_text(soup.get_text(" "))
        meta = DataQualityMetadata(source="MKK / VAP", source_url=MKK_VAP_URL, fetched_at=entry.fetched_at, confidence="medium", warnings=["Parsed from MKK/VAP public pages; official formats may change.", *warnings])
        def find_after(labels):
            for label in labels:
                m = re.search(label + r"\D{0,40}([0-9][0-9\.,]*)", text, re.I)
                if m: return parse_number(m.group(1))
            return None
        inv = find_after(["pay senedi yatırımcı sayısı", "yatırımcı sayısı", "investor count"])
        mv = find_after(["piyasa değeri", "market value"])
        foreign = find_after(["yabancı.*?oran", "foreign.*?ratio"])
        domestic = find_after(["yerli.*?oran", "domestic.*?ratio"])
        if domestic is None and foreign is not None: domestic = 100 - foreign
        return {"asset_class":"pay senedi", "investor_count": int(inv) if inv is not None else None, "market_value_try": mv, "domestic_ownership_ratio": domestic, "foreign_ownership_ratio": foreign, "metadata": meta.model_dump(mode="json")}
