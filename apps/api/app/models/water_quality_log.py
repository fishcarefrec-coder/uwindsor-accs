from datetime import date, datetime, timezone
from typing import Literal, Optional
from beanie import Document
from pydantic import Field


class WaterQualityLog(Document):
    """
    Immutable daily aquatic log.
    NEVER update, NEVER delete, NEVER soft-delete.
    Corrections are always new records.
    """
    tank_id: str
    project_id: Optional[str] = None
    type: Literal["daily", "test_strip"] = "daily"
    date: date
    parameters: dict = Field(default_factory=dict)                  # stored exactly as submitted – no in_range
    comments: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "water_quality_logs"
        indexes = [
            [("tank_id", 1), ("date", -1)],
            [("project_id", 1), ("date", -1)],
            [("date", -1)],
            [("idempotency_key", 1)],
        ]


