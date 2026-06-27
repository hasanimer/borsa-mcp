from providers.takasbank.kyp import TakasbankKypProvider
from storage.cache import CacheEntry
from datetime import UTC, datetime

class Client:
    def get_text(self, url):
        html='''<select><option>Tümü</option><option>Para Piyasası</option></select>
        Portföy İçerik Dağılımı Yatırım Fonları Emeklilik Fonları
        <table><tr><th>Pay Senedi</th><td>1.234,5</td><td>12,3</td></tr></table>'''
        return html, CacheEntry(url, datetime.now(UTC), html, '', 200, False), []

def test_kyp_options_and_records():
    p=TakasbankKypProvider(Client())
    opts=p.options()
    assert 'Portföy İçerik Dağılımı' in opts['data_types']
    assert 'Tümü' in opts['fund_types']
    recs=p.records('Portföy İçerik Dağılımı','Yatırım Fonları')
    assert recs['records'][0]['asset_class'] == 'Pay Senedi'
    assert recs['records'][0]['ratio'] == 12.3
