from providers.spk.e_veri_bankasi import SpkEVeriBankasiProvider
class SpkDataSourceService:
    def __init__(self, provider=None): self.provider = provider or SpkEVeriBankasiProvider()
    def get_data_sources(self): return self.provider.list_sources()
