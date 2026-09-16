import io
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)

# UWindsor Brand Colors per UIUX-design.md
UWINDSOR_BLUE = colors.HexColor("#005596")
UWINDSOR_GREY = colors.HexColor("#58585B")
UWINDSOR_TINT = colors.HexColor("#E6F0F7")
UWINDSOR_TEXT = colors.HexColor("#1F1F22")
BORDER_GREY = colors.HexColor("#D8D9DB")
DANGER_RED = colors.HexColor("#C0392B")
WARNING_AMBER = colors.HexColor("#D97706")


class PDFService:
    """Service to generate paper-grid PDFs and bulk export packages for ACARE facility records."""

    @staticmethod
    def _create_styles():
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'UWindsorTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=UWINDSOR_BLUE,
            alignment=0,
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            'UWindsorSubTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=13,
            textColor=UWINDSOR_GREY,
            spaceAfter=8,
        )
        header_label_style = ParagraphStyle(
            'HeaderLabel',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=UWINDSOR_TEXT,
        )
        cell_style = ParagraphStyle(
            'CellText',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=UWINDSOR_TEXT,
        )
        cell_bold_style = ParagraphStyle(
            'CellTextBold',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=UWINDSOR_TEXT,
        )
        cell_header_style = ParagraphStyle(
            'CellHeader',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=1,
        )
        return {
            'title': title_style,
            'subtitle': subtitle_style,
            'header_label': header_label_style,
            'cell': cell_style,
            'cell_bold': cell_bold_style,
            'cell_header': cell_header_style,
        }

    @staticmethod
    def generate_appendix_4b_pdf(
        room_code: str,
        pi_name: str,
        aupp_number: Optional[str] = None,
        facility_name: str = "University of Windsor Central Aquatic Facility",
        rows_data: Optional[List[Dict[str, Any]]] = None,
        generated_by: str = "System",
    ) -> bytes:
        """Generates Appendix 4b 21-Row Facility Paper-Grid PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=0.4 * inch,
            rightMargin=0.4 * inch,
            topMargin=0.4 * inch,
            bottomMargin=0.4 * inch,
        )
        story = []
        styles = PDFService._create_styles()

        # Header Block
        story.append(Paragraph("UNIVERSITY OF WINDSOR — ANIMAL CARE FACILITY", styles['subtitle']))
        story.append(Paragraph("APPENDIX 4b — DAILY AQUATIC ROOM CENSUS & MAINTENANCE LOG", styles['title']))
        story.append(HRFlowable(width="100%", thickness=2, color=UWINDSOR_BLUE, spaceBefore=2, spaceAfter=8))

        # Metadata Table
        meta_data = [
            [
                Paragraph("<b>Facility:</b> " + facility_name, styles['cell']),
                Paragraph("<b>Room Code:</b> " + (room_code or "N/A"), styles['cell']),
                Paragraph("<b>Principal Investigator:</b> " + (pi_name or "N/A"), styles['cell']),
                Paragraph("<b>AUPP #:</b> " + (aupp_number or "N/A"), styles['cell']),
            ],
            [
                Paragraph("<b>Generated:</b> " + datetime.now().strftime("%Y-%m-%d %H:%M"), styles['cell']),
                Paragraph("<b>Staff Initials:</b> " + (generated_by[:3].upper() if generated_by else "N/A"), styles['cell']),
                Paragraph("<b>Log Grid:</b> 21-Row Daily Protocol", styles['cell']),
                Paragraph("<b>Status:</b> Official Record", styles['cell']),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[2.6 * inch, 1.8 * inch, 2.5 * inch, 1.8 * inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), UWINDSOR_TINT),
            ('BOX', (0, 0), (-1, -1), 1, UWINDSOR_BLUE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # Grid Table Headers
        headers = ["Row", "Date", "Tank #", "Species", "System Temp (°C)", "pH", "DO (mg/L)", "Count", "Mortality", "Food/Feed", "Staff Init", "Observations & Maintenance Notes"]
        table_data = [[Paragraph(h, styles['cell_header']) for h in headers]]

        # Ensure exactly 21 rows for Appendix 4b paper grid specifications
        data_rows = rows_data or []
        for idx in range(1, 22):
            row_item = data_rows[idx - 1] if idx - 1 < len(data_rows) else {}
            table_data.append([
                Paragraph(str(idx), styles['cell_bold']),
                Paragraph(str(row_item.get("date", "")), styles['cell']),
                Paragraph(str(row_item.get("tank_number", "")), styles['cell']),
                Paragraph(str(row_item.get("species", "")), styles['cell']),
                Paragraph(str(row_item.get("temperature", "")), styles['cell']),
                Paragraph(str(row_item.get("ph", "")), styles['cell']),
                Paragraph(str(row_item.get("dissolved_oxygen", "")), styles['cell']),
                Paragraph(str(row_item.get("count", "")), styles['cell']),
                Paragraph(str(row_item.get("mortality", "")), styles['cell']),
                Paragraph(str(row_item.get("food", "")), styles['cell']),
                Paragraph(str(row_item.get("initials", "")), styles['cell']),
                Paragraph(str(row_item.get("notes", "")), styles['cell']),
            ])

        col_widths = [0.4 * inch, 0.9 * inch, 0.7 * inch, 0.9 * inch, 0.9 * inch, 0.5 * inch, 0.7 * inch, 0.6 * inch, 0.6 * inch, 0.8 * inch, 0.6 * inch, 2.6 * inch]
        grid_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), UWINDSOR_BLUE),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 3),
        ]
        # Alternating background colors
        for r in range(1, 22):
            if r % 2 == 0:
                t_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor("#F9FAFB")))
        grid_table.setStyle(TableStyle(t_style))

        story.append(grid_table)
        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def generate_appendix_6_pdf(
        room_code: str,
        pi_name: str,
        aupp_number: str,
        species: str,
        week_of: str,
        tanks: List[str],
        matrix_data: Optional[Dict[str, Any]] = None,
        generated_by: str = "System",
    ) -> bytes:
        """Generates Appendix 6 — Daily Water Quality Log Week Grid (Mon-Sun x Tanks) PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=0.4 * inch,
            rightMargin=0.4 * inch,
            topMargin=0.4 * inch,
            bottomMargin=0.4 * inch,
        )
        story = []
        styles = PDFService._create_styles()

        # Header Block
        story.append(Paragraph("UNIVERSITY OF WINDSOR — ANIMAL CARE FACILITY", styles['subtitle']))
        story.append(Paragraph("APPENDIX 6 — DAILY WATER QUALITY LOG (WEEKLY GRID)", styles['title']))
        story.append(HRFlowable(width="100%", thickness=2, color=UWINDSOR_BLUE, spaceBefore=2, spaceAfter=8))

        # Metadata Table
        meta_data = [
            [
                Paragraph("<b>Room:</b> " + (room_code or "N/A"), styles['cell']),
                Paragraph("<b>PI:</b> " + (pi_name or "N/A"), styles['cell']),
                Paragraph("<b>AUPP #:</b> " + (aupp_number or "N/A"), styles['cell']),
                Paragraph("<b>Species:</b> " + (species or "N/A"), styles['cell']),
                Paragraph("<b>Week Of:</b> " + (week_of or "N/A"), styles['cell']),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[1.8 * inch, 2.2 * inch, 1.8 * inch, 2.0 * inch, 2.4 * inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), UWINDSOR_TINT),
            ('BOX', (0, 0), (-1, -1), 1, UWINDSOR_BLUE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # Build Week Grid Table
        tank_headers = [f"T{t}" for t in (tanks[:14] if tanks else [str(i) for i in range(1, 15)])]
        headers = ["Day", "Metric"] + tank_headers + ["Init", "Comments"]
        table_data = [[Paragraph(h, styles['cell_header']) for h in headers]]

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        metrics = ["Temp (°C)", "pH", "D.O. (mg/L)"]
        matrix = matrix_data or {}

        for d_idx, day in enumerate(days):
            for m_idx, metric in enumerate(metrics):
                row = []
                if m_idx == 0:
                    row.append(Paragraph(f"<b>{day}</b>", styles['cell_bold']))
                else:
                    row.append(Paragraph("", styles['cell']))
                row.append(Paragraph(metric, styles['cell']))

                # Tanks values
                for t in tank_headers:
                    val = matrix.get(day, {}).get(t, {}).get(metric, "")
                    row.append(Paragraph(str(val), styles['cell']))

                # Initials & comments
                init_val = matrix.get(day, {}).get("initials", "") if m_idx == 0 else ""
                comm_val = matrix.get(day, {}).get("comments", "") if m_idx == 0 else ""
                row.append(Paragraph(str(init_val), styles['cell']))
                row.append(Paragraph(str(comm_val), styles['cell']))
                table_data.append(row)

        tank_widths = [0.45 * inch] * len(tank_headers)
        col_widths = [0.8 * inch, 0.9 * inch] + tank_widths + [0.5 * inch, 1.7 * inch]
        grid_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), UWINDSOR_BLUE),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 2),
        ]
        for d in range(len(days)):
            start_row = 1 + d * 3
            t_style.append(('SPAN', (0, start_row), (0, start_row + 2)))
            t_style.append(('SPAN', (-2, start_row), (-2, start_row + 2)))
            t_style.append(('SPAN', (-1, start_row), (-1, start_row + 2)))
            if d % 2 == 1:
                t_style.append(('BACKGROUND', (0, start_row), (-1, start_row + 2), colors.HexColor("#F9FAFB")))

        grid_table.setStyle(TableStyle(t_style))
        story.append(grid_table)

        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def generate_appendix_7_pdf(
        room_code: str,
        pi_name: str,
        aupp_number: str,
        species: str,
        logs: Optional[List[Dict[str, Any]]] = None,
        generated_by: str = "System",
    ) -> bytes:
        """Generates Appendix 7 — Water Quality Aquarium Test Strips PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            leftMargin=0.4 * inch,
            rightMargin=0.4 * inch,
            topMargin=0.4 * inch,
            bottomMargin=0.4 * inch,
        )
        story = []
        styles = PDFService._create_styles()

        # Header Block
        story.append(Paragraph("UNIVERSITY OF WINDSOR — ANIMAL CARE FACILITY", styles['subtitle']))
        story.append(Paragraph("APPENDIX 7 — AQUARIUM TEST STRIPS & PERIODIC WATER QUALITY LOG", styles['title']))
        story.append(HRFlowable(width="100%", thickness=2, color=UWINDSOR_BLUE, spaceBefore=2, spaceAfter=8))

        # Metadata Table
        meta_data = [
            [
                Paragraph("<b>Room:</b> " + (room_code or "N/A"), styles['cell']),
                Paragraph("<b>PI Name:</b> " + (pi_name or "N/A"), styles['cell']),
                Paragraph("<b>AUPP #:</b> " + (aupp_number or "N/A"), styles['cell']),
                Paragraph("<b>Species:</b> " + (species or "N/A"), styles['cell']),
                Paragraph("<b>Generated:</b> " + datetime.now().strftime("%Y-%m-%d"), styles['cell']),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[1.8 * inch, 2.2 * inch, 1.8 * inch, 2.0 * inch, 2.4 * inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), UWINDSOR_TINT),
            ('BOX', (0, 0), (-1, -1), 1, UWINDSOR_BLUE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # Schedule Banner
        sch_text = "<b>Testing Frequency Schedule:</b> Daily (Temp/DO/pH) | Bi-Weekly (Ammonia, Nitrite, Nitrate, Hardness) | Weekly (Salinity, Nitrogen) | Annually (Chlorine)"
        story.append(Paragraph(sch_text, styles['subtitle']))
        story.append(Spacer(1, 4))

        # Test Strip Data Table
        headers = ["Date", "Tank ID", "Nitrate\n(ppm)", "Nitrite\n(ppm)", "Hardness\n(ppm)", "Chlorine\n(ppm)", "Alkalinity\n(ppm)", "pH", "Ammonia\n(ppm)", "Init", "Comments & Actions Taken"]
        table_data = [[Paragraph(h, styles['cell_header']) for h in headers]]

        log_items = logs or []
        for i in range(max(15, len(log_items))):
            item = log_items[i] if i < len(log_items) else {}
            table_data.append([
                Paragraph(str(item.get("date", "")), styles['cell']),
                Paragraph(str(item.get("tank_id", "")), styles['cell']),
                Paragraph(str(item.get("nitrate", "")), styles['cell']),
                Paragraph(str(item.get("nitrite", "")), styles['cell']),
                Paragraph(str(item.get("hardness", "")), styles['cell']),
                Paragraph(str(item.get("chlorine", "")), styles['cell']),
                Paragraph(str(item.get("alkalinity", "")), styles['cell']),
                Paragraph(str(item.get("ph", "")), styles['cell']),
                Paragraph(str(item.get("ammonia", "")), styles['cell']),
                Paragraph(str(item.get("initials", "")), styles['cell']),
                Paragraph(str(item.get("comments", "")), styles['cell']),
            ])

        col_widths = [0.9 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.6 * inch, 0.8 * inch, 0.5 * inch, 2.4 * inch]
        grid_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        t_style = [
            ('BACKGROUND', (0, 0), (-1, 0), UWINDSOR_BLUE),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 3),
        ]
        for r in range(1, len(table_data)):
            if r % 2 == 0:
                t_style.append(('BACKGROUND', (0, r), (-1, r), colors.HexColor("#F9FAFB")))
        grid_table.setStyle(TableStyle(t_style))
        story.append(grid_table)

        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def generate_incident_report_pdf(
        incident_data: Dict[str, Any],
        generated_by: str = "System",
    ) -> bytes:
        """Generates Aquatic Incident Report Form PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )
        story = []
        styles = PDFService._create_styles()

        # Header Block
        story.append(Paragraph("UNIVERSITY OF WINDSOR — ANIMAL CARE FACILITY", styles['subtitle']))
        story.append(Paragraph("AQUATIC INCIDENT REPORT", styles['title']))
        story.append(HRFlowable(width="100%", thickness=2, color=UWINDSOR_BLUE, spaceBefore=2, spaceAfter=8))

        # Vet Contacted Banner if applicable
        vet_contacted = incident_data.get("vet_contacted", False)
        if vet_contacted:
            banner_data = [[
                Paragraph("<b>⚠️ ATTENTION: VETERINARIAN WAS CONTACTED FOR THIS INCIDENT</b>", ParagraphStyle('VetBanner', fontName='Helvetica-Bold', fontSize=10, textColor=colors.white, alignment=1))
            ]]
            banner_table = Table(banner_data, colWidths=[7.5 * inch])
            banner_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), DANGER_RED),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 1, DANGER_RED),
            ]))
            story.append(banner_table)
            story.append(Spacer(1, 8))

        # Details Table
        details = [
            [Paragraph("<b>Incident Date / Time:</b>", styles['cell_bold']), Paragraph(str(incident_data.get("date", "")) + " " + str(incident_data.get("time", "")), styles['cell']), Paragraph("<b>Facility / Room:</b>", styles['cell_bold']), Paragraph(str(incident_data.get("room_number", "")), styles['cell'])],
            [Paragraph("<b>Tank #:</b>", styles['cell_bold']), Paragraph(str(incident_data.get("tank_number", "")), styles['cell']), Paragraph("<b>Species:</b>", styles['cell_bold']), Paragraph(str(incident_data.get("species", "")), styles['cell'])],
            [Paragraph("<b>Principal Investigator:</b>", styles['cell_bold']), Paragraph(str(incident_data.get("pi_name", "")), styles['cell']), Paragraph("<b>AUPP #:</b>", styles['cell_bold']), Paragraph(str(incident_data.get("aupp_number", "")), styles['cell'])],
            [Paragraph("<b>Reporter:</b>", styles['cell_bold']), Paragraph(str(incident_data.get("reporter_name", generated_by)), styles['cell']), Paragraph("<b>Initials:</b>", styles['cell_bold']), Paragraph(str(incident_data.get("initials", "")), styles['cell'])],
        ]
        dt_table = Table(details, colWidths=[1.6 * inch, 2.15 * inch, 1.6 * inch, 2.15 * inch])
        dt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), UWINDSOR_TINT),
            ('BOX', (0, 0), (-1, -1), 1, UWINDSOR_BLUE),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(dt_table)
        story.append(Spacer(1, 10))

        # Checklist Flags
        chk_data = [
            [Paragraph("<b>Checklist Status</b>", styles['cell_header']), Paragraph("<b>Value</b>", styles['cell_header'])],
            [Paragraph("Researcher Notified:", styles['cell_bold']), Paragraph("Yes" if incident_data.get("researcher_notified") else "No", styles['cell'])],
            [Paragraph("Veterinarian Contacted:", styles['cell_bold']), Paragraph("Yes" if vet_contacted else "No", styles['cell'])],
            [Paragraph("Water Quality Tested:", styles['cell_bold']), Paragraph("Yes" if incident_data.get("water_quality_tested") else "No", styles['cell'])],
            [Paragraph("Quarantine Triggered:", styles['cell_bold']), Paragraph("Yes" if incident_data.get("quarantine_triggered") else "No", styles['cell'])],
        ]
        chk_table = Table(chk_data, colWidths=[5.5 * inch, 2.0 * inch])
        chk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), UWINDSOR_BLUE),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(chk_table)
        story.append(Spacer(1, 10))

        # Narrative Sections
        story.append(Paragraph("<b>Problem Description & Symptoms:</b>", styles['cell_bold']))
        story.append(Spacer(1, 2))
        prob_box = Table([[Paragraph(str(incident_data.get("problem_description", "N/A")), styles['cell'])]], colWidths=[7.5 * inch])
        prob_box.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.5, BORDER_GREY), ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAFAFA")), ('PADDING', (0, 0), (-1, -1), 6)]))
        story.append(prob_box)
        story.append(Spacer(1, 8))

        story.append(Paragraph("<b>Treatment / Immediate Action Taken:</b>", styles['cell_bold']))
        story.append(Spacer(1, 2))
        treat_box = Table([[Paragraph(str(incident_data.get("treatment_solution", "N/A")), styles['cell'])]], colWidths=[7.5 * inch])
        treat_box.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.5, BORDER_GREY), ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAFAFA")), ('PADDING', (0, 0), (-1, -1), 6)]))
        story.append(treat_box)
        story.append(Spacer(1, 8))

        story.append(Paragraph("<b>Staff Comments & Follow-Up:</b>", styles['cell_bold']))
        story.append(Spacer(1, 2))
        comm_box = Table([[Paragraph(str(incident_data.get("comments", "N/A")), styles['cell'])]], colWidths=[7.5 * inch])
        comm_box.setStyle(TableStyle([('BOX', (0, 0), (-1, -1), 0.5, BORDER_GREY), ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAFAFA")), ('PADDING', (0, 0), (-1, -1), 6)]))
        story.append(comm_box)

        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def create_bulk_export_zip(pdf_files: Dict[str, bytes]) -> bytes:
        """Packages multiple generated PDF bytes into a single downloadable ZIP archive."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for filename, content in pdf_files.items():
                zf.writestr(filename, content)
        return zip_buffer.getvalue()
