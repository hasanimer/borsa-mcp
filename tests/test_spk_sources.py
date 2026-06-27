from providers.spk.e_veri_bankasi import SpkEVeriBankasiProvider
from storage.cache import CacheEntry
from datetime import UTC, datetime

class Client:
    def get_text(self, url):
        return '<a href="/x">MKK</a><a href="https://kap.org.tr">KAP</a> Aracı Kuruluşlar', CacheEntry(url, datetime.now(UTC), '', '', 200, False), []

def test_spk_sources_parse_catalogue():
    data = SpkEVeriBankasiProvider(Client()).list_sources()
    assert 'data_sources' in data
    titles = {x['title'] for x in data['data_sources']}
    assert 'MKK' in titles
    assert 'Aracı Kuruluşlar' in titles
    assert data['metadata']['source'] == 'SPK e-Veri Bankası'
