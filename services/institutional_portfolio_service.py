from providers.takasbank.kyp import TakasbankKypProvider
class InstitutionalPortfolioService:
    def __init__(self, provider=None): self.provider=provider or TakasbankKypProvider()
    def options(self): return self.provider.options()
    def distribution(self, institutional_investor_type, fund_type="Tümü", date=None): return self.provider.records("Portföy İçerik Dağılımı", institutional_investor_type, fund_type, date)
    def fund_type_sizes(self, institutional_investor_type="Yatırım Fonları", date=None): return self.provider.records("Fon Türlerine Göre Portföy Büyüklükleri", institutional_investor_type, "Tümü", date)
    def compare_types(self, investor_types=None, date=None):
        investor_types=investor_types or ["Yatırım Fonları","Emeklilik Fonları","Gayrimenkul Yatırım Fonu","Girişim Sermayesi Yatırım Fonu"]
        return {"comparisons":[self.distribution(t, date=date) for t in investor_types]}
    def equity_exposure(self, institutional_investor_type="Yatırım Fonları", fund_type="Tümü", date=None):
        data=self.distribution(institutional_investor_type, fund_type, date)
        if "records" in data:
            data["records"]=[r for r in data["records"] if "pay" in (r.get("asset_class") or "").lower() or "hisse" in (r.get("asset_class") or "").lower()]
            if not data["records"]: data["warnings"]=["No equity exposure row was detected in parsed KYP records."]
        return data
