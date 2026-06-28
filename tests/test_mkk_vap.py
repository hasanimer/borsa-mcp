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


class OutOfRangeRatioClient:
    """Foreign-ratio label followed by a non-ratio (market-value) number."""
    def get_text(self, url):
        html='Yabancı Oran ile ilgili Piyasa Değeri 2.500.000 TL'
        return html, CacheEntry(url, datetime.now(UTC), html, '', 200, False), []


def test_mkk_rejects_out_of_range_ownership_ratio():
    data=MkkVapProvider(OutOfRangeRatioClient()).market_summary()
    # 2.500.000 is not a plausible 0-100 ratio, so it is discarded rather than
    # reported as a bogus ownership ratio (and domestic is not derived from it).
    assert data['foreign_ownership_ratio'] is None
    assert data['domestic_ownership_ratio'] is None
