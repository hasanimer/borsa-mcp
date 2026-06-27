from services.spk_data_source_service import SpkDataSourceService

def register(app):
    @app.tool(name="get_spk_data_sources", title="SPK Data Sources", description="List official SPK e-Veri Bankası source catalogue entries.", tags={"spk","official"}, annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_spk_data_sources():
        return SpkDataSourceService().get_data_sources()
