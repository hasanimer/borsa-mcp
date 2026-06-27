from __future__ import annotations
from bs4 import BeautifulSoup
from domain.models import DataQualityMetadata, KypOptions, KypPortfolioRecord, StructuredError
from domain.normalizers import clean_text, parse_number
from .client import TAKASBANK_KYP_URL, TakasbankClient

DEFAULT_DATA_TYPES=["Portföy İçerik Dağılımı","Fon Türlerine Göre Portföy Büyüklükleri"]
DEFAULT_INVESTOR_TYPES=["Yatırım Fonları","Emeklilik Fonları","Borsa Yatırım Fonları","Yatırım Ortaklıkları","Girişim Sermayesi Yatırım Fonu","Gayrimenkul Yatırım Fonu"]

class TakasbankKypProvider:
    def __init__(self, client: TakasbankClient | None=None): self.client=client or TakasbankClient(cache_ttl=3600)
    def _soup_meta(self):
        html, entry, warnings = self.client.get_text(TAKASBANK_KYP_URL)
        meta=DataQualityMetadata(source="Takasbank KYP", source_url=TAKASBANK_KYP_URL, fetched_at=entry.fetched_at, confidence="medium", warnings=["Takasbank KYP is institutional portfolio/fund portfolio distribution data, not individual investor-count data.", *warnings])
        return BeautifulSoup(html,"html.parser"), meta
    def options(self):
        try: soup, meta=self._soup_meta()
        except Exception as exc: return StructuredError(error="takasbank_kyp_fetch_failed", message=str(exc), source="Takasbank KYP", source_url=TAKASBANK_KYP_URL, warnings=["KYP page could not be fetched."]).model_dump(mode="json")
        opts=[]
        for sel in soup.select("select"):
            vals=[clean_text(o.get_text(" ")) for o in sel.select("option") if clean_text(o.get_text(" "))]
            opts.extend(vals)
        text=clean_text(soup.get_text(" "))
        data=[x for x in DEFAULT_DATA_TYPES if x in text or x in opts] or DEFAULT_DATA_TYPES
        inv=[x for x in DEFAULT_INVESTOR_TYPES if x in text or x in opts] or DEFAULT_INVESTOR_TYPES
        fund=sorted({x for x in opts if x not in data and x not in inv}) or ["Tümü"]
        return KypOptions(data_types=data, institutional_investor_types=inv, fund_types=fund, metadata=meta).model_dump(mode="json")
    def records(self, data_type: str, institutional_investor_type: str | None=None, fund_type: str | None="Tümü", date: str | None=None):
        try: soup, meta=self._soup_meta()
        except Exception as exc: return StructuredError(error="takasbank_kyp_fetch_failed", message=str(exc), source="Takasbank KYP", source_url=TAKASBANK_KYP_URL, warnings=["KYP page could not be fetched."]).model_dump(mode="json")
        rows=[]
        for tr in soup.select("tr"):
            cells=[clean_text(c.get_text(" ")) for c in tr.select("th,td")]
            if len(cells)>=2:
                rows.append(KypPortfolioRecord(data_type=data_type, institutional_investor_type=institutional_investor_type, fund_type=fund_type, asset_class=cells[0], portfolio_size_try=parse_number(cells[1]), ratio=parse_number(cells[2]) if len(cells)>2 else None, date=date, metadata=meta))
        if not rows:
            return StructuredError(error="takasbank_kyp_parse_unavailable", message="No KYP table rows or reliable dynamic endpoint could be parsed from the current page.", source="Takasbank KYP", source_url=TAKASBANK_KYP_URL, warnings=[*meta.warnings, "The page may rely on JavaScript or an endpoint that changed."]).model_dump(mode="json")
        return {"records":[r.model_dump(mode="json") for r in rows], "metadata":meta.model_dump(mode="json")}
