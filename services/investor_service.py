from providers.mkk.vap import MkkVapProvider
from providers.mkk.investor_counts import MkkInvestorCountsProvider
from domain.models import DataQualityMetadata, DomesticForeignOwnershipRecord
from providers.mkk.client import MKK_VAP_URL

class InvestorService:
    def __init__(self, vap=None, counts=None): self.vap=vap or MkkVapProvider(); self.counts=counts or MkkInvestorCountsProvider()
    def equity_summary(self): return self.vap.market_summary()
    def domestic_foreign_ownership(self):
        s=self.equity_summary()
        if "error" in s: return s
        m=s["metadata"]
        rec=DomesticForeignOwnershipRecord(date=m.get("as_of_date"), asset_class=s.get("asset_class","pay senedi"), domestic_ownership_ratio=s.get("domestic_ownership_ratio"), foreign_ownership_ratio=s.get("foreign_ownership_ratio"), metadata=DataQualityMetadata(**m))
        return {"records":[rec.model_dump(mode="json")], "metadata":m}
    def top_stocks_by_investor_count(self, limit=10): return self.counts.stock_level_unavailable()
    def stock_investor_trend(self, symbol): return self.counts.stock_level_unavailable(symbol)
