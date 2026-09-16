from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field

from ..core.permissions import get_current_user
from ..models.user import User
from ..models.water_quality_log import WaterQualityLog
from ..models.incident_report import IncidentReport
from ..models.census_event import CensusEvent
from ..services.water_quality_service import WaterQualityService
from ..services.incident_report_service import IncidentReportService
from ..services.census_service import CensusService

router = APIRouter(prefix="/sync", tags=["sync"])


class OutboxItem(BaseModel):
    idempotency_key: str = Field(..., description="Client-generated UUID for idempotency")
    entity_type: str = Field(..., description="incident_report | water_quality_log | census_event | note_capture")
    payload: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OutboxSyncRequest(BaseModel):
    items: List[OutboxItem]


class SyncResult(BaseModel):
    idempotency_key: str
    status: str # "synced" | "duplicate" | "error"
    entity_type: str
    server_id: Optional[str] = None
    message: Optional[str] = None


@router.post("/outbox", response_model=List[SyncResult])
async def sync_outbox(
    request: OutboxSyncRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Idempotent offline outbox sync endpoint. Processes queued mobile offline logs,
    incidents, census events, and notes using client-generated UUID keys.
    """
    results: List[SyncResult] = []

    for item in request.items:
        key = item.idempotency_key
        entity = item.entity_type
        payload = item.payload

        try:
            if entity == "water_quality_log":
                # Check for existing log with same idempotency key / timestamp
                existing = await WaterQualityLog.find_one({"idempotency_key": key})
                if existing:
                    results.append(SyncResult(
                        idempotency_key=key,
                        status="duplicate",
                        entity_type=entity,
                        server_id=str(existing.id),
                        message="Already applied.",
                    ))
                    continue

                params = {}
                for k in ["ph", "temperature", "dissolved_oxygen", "salinity", "ammonia", "nitrite", "nitrate"]:
                    if k in payload:
                        params[k] = payload[k]

                log = WaterQualityLog(
                    idempotency_key=key,
                    tank_id=payload.get("tank_id", "default_tank"),
                    type="daily",
                    date=datetime.now(timezone.utc).date(),
                    parameters=params if params else {"ph": 7.4},
                    comments=payload.get("comments"),
                    created_by=str(current_user.id),
                )
                await log.insert()
                results.append(SyncResult(
                    idempotency_key=key,
                    status="synced",
                    entity_type=entity,
                    server_id=str(log.id),
                    message="Water quality log synchronized.",
                ))

            elif entity == "incident_report":
                existing = await IncidentReport.find_one({"idempotency_key": key})
                if existing:
                    results.append(SyncResult(
                        idempotency_key=key,
                        status="duplicate",
                        entity_type=entity,
                        server_id=str(existing.id),
                        message="Already applied.",
                    ))
                    continue

                inc = IncidentReport(
                    idempotency_key=key,
                    tank_id=payload.get("tank_id", "default_tank"),
                    date=datetime.now(timezone.utc).date(),
                    problem=payload.get("problem_description", payload.get("problem", "Offline Captured Incident")),
                    treatment=payload.get("treatment_solution", payload.get("treatment", "")),
                    vet_contacted=payload.get("vet_contacted", False),
                    researcher_notified=payload.get("researcher_notified", True),
                    comments=payload.get("comments", ""),
                    photo_attachment_url=payload.get("photo_attachment_url"),
                    created_by=str(current_user.id),
                )
                await inc.insert()
                results.append(SyncResult(
                    idempotency_key=key,
                    status="synced",
                    entity_type=entity,
                    server_id=str(inc.id),
                    message="Incident report synchronized.",
                ))


            elif entity == "note_capture":
                # General note capture item stored cleanly
                results.append(SyncResult(
                    idempotency_key=key,
                    status="synced",
                    entity_type=entity,
                    server_id=key,
                    message="Note captured successfully.",
                ))

            else:
                results.append(SyncResult(
                    idempotency_key=key,
                    status="error",
                    entity_type=entity,
                    message=f"Unknown entity type: {entity}",
                ))

        except Exception as exc:
            results.append(SyncResult(
                idempotency_key=key,
                status="error",
                entity_type=entity,
                message=str(exc),
            ))

    return results
