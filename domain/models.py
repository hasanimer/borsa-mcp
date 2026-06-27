from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Confidence = Literal["high", "medium", "low"]


class DataQualityMetadata(BaseModel):
    source: str
    source_url: str
    as_of_date: str | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    confidence: Confidence = "medium"
    warnings: list[str] = Field(default_factory=list)


class StructuredError(BaseModel):
    error: str
    message: str
    source: str
    source_url: str | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    confidence: Confidence = "low"
    warnings: list[str] = Field(default_factory=list)


class SpkDataSource(BaseModel):
    category: str
    institution: str | None = None
    title: str
    url: str | None = None
    metadata: DataQualityMetadata


class EquityInvestorSummary(BaseModel):
    asset_class: str
    investor_count: int | None = None
    market_value_try: float | None = None
    domestic_ownership_ratio: float | None = None
    foreign_ownership_ratio: float | None = None
    metadata: DataQualityMetadata


class DomesticForeignOwnershipRecord(BaseModel):
    date: str | None = None
    asset_class: str
    domestic_ownership_ratio: float | None = None
    foreign_ownership_ratio: float | None = None
    metadata: DataQualityMetadata


class StockInvestorCountRecord(BaseModel):
    symbol: str
    date: str | None = None
    investor_count: int | None = None
    metadata: DataQualityMetadata


class KypPortfolioRecord(BaseModel):
    data_type: str
    institutional_investor_type: str | None = None
    fund_type: str | None = None
    asset_class: str | None = None
    portfolio_size_try: float | None = None
    ratio: float | None = None
    date: str | None = None
    metadata: DataQualityMetadata


class KypOptions(BaseModel):
    data_types: list[str] = Field(default_factory=list)
    institutional_investor_types: list[str] = Field(default_factory=list)
    fund_types: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    metadata: DataQualityMetadata
