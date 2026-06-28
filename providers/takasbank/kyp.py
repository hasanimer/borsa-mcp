from __future__ import annotations
from bs4 import BeautifulSoup
from domain.enums import KypDataType
from domain.models import DataQualityMetadata, KypOptions, KypPortfolioRecord, StructuredError
from domain.normalizers import clean_text, parse_number
from .client import TAKASBANK_KYP_URL, TakasbankClient

DEFAULT_DATA_TYPES=[KypDataType.PORTFOLIO_DISTRIBUTION.value, KypDataType.FUND_TYPE_SIZES.value]
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
    @staticmethod
    def _tables_for(soup, data_type: str):
        """Return the table(s) whose nearby heading/caption matches data_type.

        Falls back to every table when no heading matches, so single-table or
        unlabelled server-rendered pages still parse. This is what lets
        'Portföy İçerik Dağılımı' and 'Fon Türlerine Göre Portföy Büyüklükleri'
        return their own rows instead of a merged dump of every <tr> on the page.
        """
        tables=soup.select("table")
        if not tables: return []
        needle=clean_text(data_type).lower()
        if not needle: return tables
        matched=[]
        for table in tables:
            cap=table.find("caption")
            context=clean_text(cap.get_text(" ")) if cap else ""
            prev=table.find_previous(["h1","h2","h3","h4","h5","h6","caption","summary","legend","strong","b","p"])
            if prev: context=f"{context} {clean_text(prev.get_text(' '))}"
            if needle in context.lower(): matched.append(table)
        return matched or tables
    def records(self, data_type: str, institutional_investor_type: str | None=None, fund_type: str | None="Tümü", date: str | None=None):
        try: soup, meta=self._soup_meta()
        except Exception as exc: return StructuredError(error="takasbank_kyp_fetch_failed", message=str(exc), source="Takasbank KYP", source_url=TAKASBANK_KYP_URL, warnings=["KYP page could not be fetched."]).model_dump(mode="json")
        rows=[]
        for table in self._tables_for(soup, data_type):
            for tr in table.select("tr"):
                cells=[clean_text(c.get_text(" ")) for c in tr.select("th,td")]
                if len(cells)<2: continue
                size=parse_number(cells[1])
                ratio=parse_number(cells[2]) if len(cells)>2 else None
                if size is None and ratio is None: continue  # header / label-only / non-numeric row
                rows.append(KypPortfolioRecord(data_type=data_type, institutional_investor_type=institutional_investor_type, fund_type=fund_type, asset_class=cells[0], portfolio_size_try=size, ratio=ratio, date=date, metadata=meta))
        if not rows:
            return StructuredError(error="takasbank_kyp_parse_unavailable", message="No KYP table rows or reliable dynamic endpoint could be parsed from the current page.", source="Takasbank KYP", source_url=TAKASBANK_KYP_URL, warnings=[*meta.warnings, "The page may rely on JavaScript or an endpoint that changed."]).model_dump(mode="json")
        return {"records":[r.model_dump(mode="json") for r in rows], "metadata":meta.model_dump(mode="json")}
