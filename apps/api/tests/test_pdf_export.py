import pytest
from app.services.pdf_service import PDFService


def test_pdf_service_appendix_4b_generation():
    pdf_bytes = PDFService.generate_appendix_4b_pdf(
        room_code="101",
        pi_name="Dr. Jane Smith",
        aupp_number="AUPP-2026-999",
        generated_by="Admin User",
    )
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_service_appendix_6_generation():
    pdf_bytes = PDFService.generate_appendix_6_pdf(
        room_code="102",
        pi_name="Dr. John Doe",
        aupp_number="AUPP-2026-888",
        species="Medaka",
        week_of="2026-W38",
        tanks=["1", "2", "3", "4"],
        generated_by="Staff Tech",
    )
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_service_appendix_7_generation():
    pdf_bytes = PDFService.generate_appendix_7_pdf(
        room_code="101",
        pi_name="Dr. Jane Smith",
        aupp_number="AUPP-2026-999",
        species="Zebrafish",
        generated_by="Staff Tech",
    )
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_service_incident_report_generation():
    incident = {
        "date": "2026-09-16",
        "time": "10:30",
        "room_number": "101",
        "tank_number": "Tank 2",
        "species": "Zebrafish",
        "pi_name": "Dr. Jane Smith",
        "aupp_number": "AUPP-2026-999",
        "reporter_name": "Staff Tech",
        "initials": "ST",
        "researcher_notified": True,
        "vet_contacted": True,
        "water_quality_tested": True,
        "quarantine_triggered": False,
        "problem_description": "Water clarity issue.",
        "treatment_solution": "Replaced filter pad.",
        "comments": "Observed for 30 minutes post-fix.",
    }
    pdf_bytes = PDFService.generate_incident_report_pdf(incident, generated_by="Staff Tech")
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_service_bulk_zip_creation():
    files = {
        "doc1.pdf": PDFService.generate_appendix_4b_pdf("101", "PI A", "AUPP 1"),
        "doc2.pdf": PDFService.generate_appendix_6_pdf("101", "PI A", "AUPP 1", "Zebrafish", "2026-W38", ["1"]),
    }
    zip_bytes = PDFService.create_bulk_export_zip(files)
    assert zip_bytes is not None
    assert len(zip_bytes) > 0
    # ZIP magic header PK\x03\x04
    assert zip_bytes.startswith(b"PK\x03\x04")
