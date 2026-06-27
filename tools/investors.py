from typing import Annotated
from pydantic import Field
from services.investor_service import InvestorService

def register(app):
    @app.tool(name="get_equity_investor_summary", title="Equity Investor Summary", description="Get MKK/VAP equity-market investor summary.", tags={"mkk","investors"}, annotations={"readOnlyHint": True, "openWorldHint": True})
    async def get_equity_investor_summary(): return InvestorService().equity_summary()
    @app.tool(name="get_domestic_foreign_ownership", title="Domestic/Foreign Ownership", description="Get domestic/foreign ownership ratios from MKK/VAP.", tags={"mkk","investors"}, annotations={"readOnlyHint": True})
    async def get_domestic_foreign_ownership(): return InvestorService().domestic_foreign_ownership()
    @app.tool(name="get_top_stocks_by_investor_count", title="Top Stocks By Investor Count", description="Get stock-level investor counts if officially available; otherwise structured error.", tags={"mkk","investors"}, annotations={"readOnlyHint": True})
    async def get_top_stocks_by_investor_count(limit: Annotated[int, Field(default=10, ge=1, le=100)] = 10): return InvestorService().top_stocks_by_investor_count(limit)
    @app.tool(name="get_stock_investor_trend", title="Stock Investor Trend", description="Get stock-level investor-count trend if officially available; otherwise structured error.", tags={"mkk","investors"}, annotations={"readOnlyHint": True})
    async def get_stock_investor_trend(symbol: Annotated[str, Field(min_length=2, examples=["THYAO"])]): return InvestorService().stock_investor_trend(symbol)
