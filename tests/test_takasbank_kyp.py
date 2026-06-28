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


class TwoTableClient:
    """Server-rendered page with a labelled table per data type plus header rows."""
    def get_text(self, url):
        html='''
        <h3>Portföy İçerik Dağılımı</h3>
        <table>
          <tr><th>Varlık Sınıfı</th><th>Büyüklük</th><th>Oran</th></tr>
          <tr><td>Pay Senedi</td><td>1.000,0</td><td>25,0</td></tr>
          <tr><td>Borçlanma Araçları</td><td>3.000,0</td><td>75,0</td></tr>
        </table>
        <h3>Fon Türlerine Göre Portföy Büyüklükleri</h3>
        <table>
          <tr><th>Fon Türü</th><th>Büyüklük</th></tr>
          <tr><td>Hisse Fonu</td><td>5.000,0</td></tr>
        </table>'''
        return html, CacheEntry(url, datetime.now(UTC), html, '', 200, False), []


def test_kyp_records_scoped_to_data_type_table_and_skip_header_rows():
    p=TakasbankKypProvider(TwoTableClient())
    dist=p.records('Portföy İçerik Dağılımı','Yatırım Fonları')
    # only the matching table's data rows; the <th> header row is dropped, the
    # second table ('Fon Türleri...') is excluded.
    assert [r['asset_class'] for r in dist['records']] == ['Pay Senedi','Borçlanma Araçları']
    assert dist['records'][0]['portfolio_size_try'] == 1000.0
    sizes=p.records('Fon Türlerine Göre Portföy Büyüklükleri','Yatırım Fonları')
    assert [r['asset_class'] for r in sizes['records']] == ['Hisse Fonu']
