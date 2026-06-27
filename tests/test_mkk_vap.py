from providers.mkk.vap import MkkVapProvider
from services.investor_service import InvestorService
from storage.cache import CacheEntry
from datetime import UTC, datetime

class Client:
    def get_text(self, url):
        html='Pay senedi yatırımcı sayısı 1.234.567 Piyasa Değeri 2.500,50 Yabancı Oran 38,5'
        return html, CacheEntry(url, datetime.now(UTC), html, '', 200, False), []

def test_mkk_equity_summary_parse():
    data=MkkVapProvider(Client()).market_summary()
    assert data['investor_count'] == 1234567
    assert data['foreign_ownership_ratio'] == 38.5
    assert data['domestic_ownership_ratio'] == 61.5
    assert data['metadata']['source'] == 'MKK / VAP'

def test_stock_level_returns_structured_error():
    data=InvestorService(vap=MkkVapProvider(Client())).top_stocks_by_investor_count()
    assert data['error'] == 'stock_level_investor_count_not_available'
