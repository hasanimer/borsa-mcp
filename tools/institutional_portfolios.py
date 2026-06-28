from services.institutional_portfolio_service import InstitutionalPortfolioService
from tools._runtime import run_tool

_service = InstitutionalPortfolioService()

def register(app):
    @app.tool(name="get_takasbank_kyp_options", title="Takasbank KYP Options", description="Return dropdown/options discovered from Takasbank KYP.", tags={"takasbank","kyp"}, annotations={"readOnlyHint": True})
    async def get_takasbank_kyp_options(): return await run_tool(_service.options)
    @app.tool(name="get_institutional_portfolio_distribution", title="Institutional Portfolio Distribution", description="Get KYP portfolio asset-class distribution.", tags={"takasbank","kyp"}, annotations={"readOnlyHint": True})
    async def get_institutional_portfolio_distribution(institutional_investor_type: str, fund_type: str="Tümü", date: str|None=None): return await run_tool(_service.distribution, institutional_investor_type, fund_type, date)
    @app.tool(name="get_fund_type_portfolio_sizes", title="Fund Type Portfolio Sizes", description="Get KYP portfolio sizes by fund type.", tags={"takasbank","kyp"}, annotations={"readOnlyHint": True})
    async def get_fund_type_portfolio_sizes(institutional_investor_type: str="Yatırım Fonları", date: str|None=None): return await run_tool(_service.fund_type_sizes, institutional_investor_type, date)
    @app.tool(name="compare_institutional_investor_types", title="Compare Institutional Investor Types", description="Compare KYP institutional investor categories.", tags={"takasbank","kyp"}, annotations={"readOnlyHint": True})
    async def compare_institutional_investor_types(investor_types: list[str]|None=None, date: str|None=None): return await run_tool(_service.compare_types, investor_types, date)
    @app.tool(name="get_institutional_equity_exposure", title="Institutional Equity Exposure", description="Get equity exposure/share in institutional portfolios if available.", tags={"takasbank","kyp"}, annotations={"readOnlyHint": True})
    async def get_institutional_equity_exposure(institutional_investor_type: str="Yatırım Fonları", fund_type: str="Tümü", date: str|None=None): return await run_tool(_service.equity_exposure, institutional_investor_type, fund_type, date)
