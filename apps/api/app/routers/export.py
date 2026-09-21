from datetime import date, datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse

from ..core.permissions import require_manager_plus
from ..models.user import User
from ..services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["export"])


def _validate_range(start_date: Optional[date], end_date: Optional[date]) -> None:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(422, "start_date must be on or before end_date")


@router.get("/preview")
async def preview_export(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current: User = Depends(require_manager_plus),
):
    _validate_range(start_date, end_date)
    record_counts = await ExportService.get_preview_counts(start_date, end_date)
    return {
        "record_counts": record_counts,
        "start_date": start_date,
        "end_date": end_date,
    }


@router.get("/backup")
async def download_backup(
    export_format: str = Query(..., alias="format", pattern="^(json|csv)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current: User = Depends(require_manager_plus),
):
    _validate_range(start_date, end_date)

    try:
        bundle = await ExportService.build_export_bundle(start_date, end_date)
    except Exception as exc:
        raise HTTPException(500, f"Export failed while building the data bundle: {exc}")

    record_counts = {name: len(rows) for name, rows in bundle.items()}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if export_format == "json":
        content = ExportService.generate_json_export(bundle)
        await ExportService.write_export_audit_log(current, "json", start_date, end_date, record_counts)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=acare_backup_{today}.json"},
        )

    if start_date or end_date:
        scope = f"{start_date.isoformat() if start_date else 'Beginning'} to {end_date.isoformat() if end_date else 'Now'}"
    else:
        scope = "Full Backup"
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "actor_name": f"{current.first_name} {current.last_name}".strip(),
        "scope": scope,
    }
    zip_buffer = ExportService.generate_csv_export(bundle, meta)
    await ExportService.write_export_audit_log(current, "csv", start_date, end_date, record_counts)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=acare_backup_{today}.zip"},
    )


@router.get("/pdf-grid")
async def download_pdf_grid(
    form_type: str = Query(..., pattern="^(appendix_4b|appendix_6|appendix_7|incident)$"),
    room_code: Optional[str] = Query("101"),
    pi_name: Optional[str] = Query("Dr. Windsor"),
    aupp_number: Optional[str] = Query("AUPP-2026-001"),
    species: Optional[str] = Query("Zebrafish"),
    week_of: Optional[str] = Query("2026-W38"),
    incident_id: Optional[str] = Query(None),
    current: User = Depends(require_manager_plus),
):
    """Generates a PDF paper grid matching facility physical paper forms."""
    from ..services.pdf_service import PDFService
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    actor = f"{current.first_name} {current.last_name}".strip()

    if form_type == "appendix_4b":
        pdf_bytes = PDFService.generate_appendix_4b_pdf(
            room_code=room_code or "101",
            pi_name=pi_name or "Dr. Windsor",
            aupp_number=aupp_number or "AUPP-2026-001",
            generated_by=actor,
        )
        filename = f"Appendix_4b_Census_Room_{room_code}_{today_str}.pdf"

    elif form_type == "appendix_6":
        tanks = [str(i) for i in range(1, 15)]
        pdf_bytes = PDFService.generate_appendix_6_pdf(
            room_code=room_code or "101",
            pi_name=pi_name or "Dr. Windsor",
            aupp_number=aupp_number or "AUPP-2026-001",
            species=species or "Zebrafish",
            week_of=week_of or "2026-W38",
            tanks=tanks,
            generated_by=actor,
        )
        filename = f"Appendix_6_WaterQuality_Room_{room_code}_{today_str}.pdf"

    elif form_type == "appendix_7":
        pdf_bytes = PDFService.generate_appendix_7_pdf(
            room_code=room_code or "101",
            pi_name=pi_name or "Dr. Windsor",
            aupp_number=aupp_number or "AUPP-2026-001",
            species=species or "Zebrafish",
            generated_by=actor,
        )
        filename = f"Appendix_7_TestStrips_Room_{room_code}_{today_str}.pdf"

    else: # incident
        dummy_incident = {
            "date": today_str,
            "time": "14:30",
            "room_number": room_code or "101",
            "tank_number": "Tank 4",
            "species": species or "Zebrafish",
            "pi_name": pi_name or "Dr. Windsor",
            "aupp_number": aupp_number or "AUPP-2026-001",
            "reporter_name": actor,
            "initials": current.first_name[0] + current.last_name[0] if current.first_name and current.last_name else "SW",
            "researcher_notified": True,
            "vet_contacted": True,
            "water_quality_tested": True,
            "quarantine_triggered": False,
            "problem_description": "Elevated nitrite detected in system recirculation line. Fish exhibiting slight lethargy.",
            "treatment_solution": "Flushed biofilter line, replaced 25% water volume, notified lab tech.",
            "comments": "Follow-up reading scheduled for 08:00 tomorrow morning.",
        }
        pdf_bytes = PDFService.generate_incident_report_pdf(dummy_incident, generated_by=actor)
        filename = f"Aquatic_Incident_Report_{today_str}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/bulk-pdf")
async def download_bulk_pdf_zip(
    room_codes: List[str] = Query(default=["101", "102"]),
    current: User = Depends(require_manager_plus),
):
    """Generates a ZIP bundle containing full paper-grid export forms across specified rooms."""
    from ..services.pdf_service import PDFService
    actor = f"{current.first_name} {current.last_name}".strip()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    files = {}
    for room in room_codes:
        files[f"Appendix_4b_Room_{room}_{today_str}.pdf"] = PDFService.generate_appendix_4b_pdf(
            room_code=room, pi_name="Dr. Windsor", aupp_number="AUPP-2026-001", generated_by=actor
        )
        files[f"Appendix_6_Room_{room}_{today_str}.pdf"] = PDFService.generate_appendix_6_pdf(
            room_code=room, pi_name="Dr. Windsor", aupp_number="AUPP-2026-001", species="Zebrafish", week_of="2026-W38", tanks=[str(i) for i in range(1, 15)], generated_by=actor
        )
        files[f"Appendix_7_Room_{room}_{today_str}.pdf"] = PDFService.generate_appendix_7_pdf(
            room_code=room, pi_name="Dr. Windsor", aupp_number="AUPP-2026-001", species="Zebrafish", generated_by=actor
        )

    zip_bytes = PDFService.create_bulk_export_zip(files)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=ACARE_PaperGrid_Bundle_{today_str}.zip"},
    )

