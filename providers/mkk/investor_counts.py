from domain.models import StructuredError
from .client import MKK_VAP_URL

class MkkInvestorCountsProvider:
    def stock_level_unavailable(self, symbol: str | None = None):
        return StructuredError(error="stock_level_investor_count_not_available", message="The current source exposes market-level investor data but not stock-level investor count.", source="MKK / VAP", source_url=MKK_VAP_URL, warnings=["No volume, market-cap, popularity, or transaction-count proxy was substituted for investor count.", "If MKK/VAP exposes a stock-level endpoint in the future, this tool should be wired to that official endpoint."]).model_dump(mode="json")
