from __future__ import annotations

from domain.models import DataQualityMetadata


def with_warning(metadata: DataQualityMetadata, warning: str) -> DataQualityMetadata:
    """Return metadata with an additional warning, preserving existing fields."""
    data = metadata.model_dump()
    data["warnings"] = [*metadata.warnings, warning]
    return DataQualityMetadata(**data)
