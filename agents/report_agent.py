"""
Report Assembly Agent
Structures and compiles medical reports into PDF
"""

from typing import Dict, List, Tuple
import os
from datetime import datetime
from loguru import logger
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Frame, PageTemplate
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class ReportAssemblyAgent:
    """
    Specialized agent for assembling structured medical reports.
    Compiles extracted content into a professional, formatted PDF document
    with consolidated tables and a clear structure.
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        logger.info("Report Assembly Agent initialized")

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        # Title style for the cover page
        self.styles.add(ParagraphStyle(
            name='CustomTitle', parent=self.styles['h1'], fontSize=28,
            textColor=colors.HexColor('#1f77b4'), alignment=TA_CENTER, spaceAfter=20
        ))
        # Subtitle style for the cover page
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle', parent=self.styles['h2'], fontSize=16,
            textColor=colors.HexColor('#566573'), alignment=TA_CENTER, spaceAfter=40
        ))
        # Section heading style
        self.styles.add(ParagraphStyle(
            name='SectionHeading', parent=self.styles['h2'], fontSize=16,
            textColor=colors.HexColor('#2c3e50'), spaceBefore=18, spaceAfter=12, keepWithNext=1
        ))
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody', parent=self.styles['BodyText'], fontSize=11,
            leading=15, alignment=TA_LEFT, spaceAfter=6
        ))
        # Footer text style
        self.styles.add(ParagraphStyle(
            name='FooterStyle', parent=self.styles['Normal'], fontSize=9,
            textColor=colors.grey, alignment=TA_CENTER
        ))
        # Table title style
        self.styles.add(ParagraphStyle(
            name='TableTitle', parent=self.styles['h4'], fontSize=11,
            textColor=colors.HexColor('#34495E'), alignment=TA_LEFT, spaceBefore=10, spaceAfter=5
        ))

    def _header_footer(self, canvas, doc):
        """Draws the header and footer on each page."""
        canvas.saveState()
        # Header
        header = Paragraph("The Generated Report", self.styles['Normal'])
        w, h = header.wrap(doc.width, doc.topMargin)
        # header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
        header.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin + (0.3 * inch))
        
        # Footer
        footer_text = f"Page {doc.page}"
        footer = Paragraph(footer_text, self.styles['FooterStyle'])
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, h)
        canvas.restoreState()

    def _clean_text(self, text: str) -> str:
        """Clean and format text for PDF to prevent rendering errors."""
        text = " ".join(text.split()) # Remove excessive whitespace
        # Escape special XML/HTML characters
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return text

    def _build_tables_section(self, story: List, all_tables: List[Tuple[str, Dict]]):
        """Builds the consolidated tables section of the report."""
        if not all_tables:
            return

        story.append(PageBreak())
        story.append(Paragraph("Patient Tables", self.styles['SectionHeading']))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            "The following tables have been extracted from the source documents.",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 0.2 * inch))

        current_source_section = ""
        for i, (source_section, table_info) in enumerate(all_tables, 1):
            # Add a sub-heading for the source section if it's new
            if source_section != current_source_section:
                story.append(Paragraph(f"<b>Tables from:</b> {source_section}", self.styles['TableTitle']))
                current_source_section = source_section

            table_data = table_info.get("data")
            if not table_data or not isinstance(table_data, list) or len(table_data) < 1:
                continue

            # Create and style the table
            t = Table(table_data, repeatRows=1, hAlign='LEFT')
            t.setStyle(TableStyle([
                # Header Style
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                # Zebra Stripes
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F2F2F2')),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                # Body Style
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.3 * inch))

    async def assemble_report(
        self,
        session_id: str,
        extracted_content: Dict[str, Dict],
        sections: List[str]
    ) -> str:
        """
        Assembles a structured PDF report from extracted content.

        Args:
            session_id: The unique session identifier.
            extracted_content: A dictionary mapping section names to their content.
            sections: An ordered list of sections to include in the report.

        Returns:
            The file path to the generated PDF report.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"medical_report_{session_id[:8]}_{timestamp}.pdf"
            filepath = os.path.join("reports", filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch)
            story = []

            # === 1. Title Page ===
            report_date = datetime.now().strftime("%B %d, %Y")
            story.append(Paragraph("Medical Report", self.styles['CustomTitle']))
            story.append(Paragraph("Generated from Uploaded Patient Documents", self.styles['CustomSubtitle']))
            story.append(Spacer(1, 2 * inch))
            story.append(Paragraph(f"<b>Date Generated:</b> {report_date}", self.styles['CustomBody']))
            story.append(Paragraph(f"<b>Report ID:</b> {session_id[:8]}", self.styles['CustomBody']))
            story.append(Spacer(1, 0.5 * inch))
            story.append(Paragraph(
                "<i>This is an automatically generated report. Always verify findings with original source documents.</i>",
                self.styles['FooterStyle']
            ))
            story.append(PageBreak())

            # === 2. Report Contents (Table of Contents) ===
            story.append(Paragraph("Report Contents", self.styles['SectionHeading']))
            for section_name in sections:
                story.append(Paragraph(f"• &nbsp; {section_name}", self.styles['CustomBody']))
            story.append(Spacer(1, 0.3 * inch))

            # === 3. Aggregate all tables from content ===
            all_tables = []
            for section_name, content in extracted_content.items():
                if "tables" in content and content["tables"]:
                    for table_info in content["tables"]:
                        all_tables.append((section_name, table_info))

            # === 4. Build Sections ===
            for section in sections:
                if section == "Patient Tables":
                    # This section is special and will be built from all aggregated tables
                    self._build_tables_section(story, all_tables)
                    continue

                content = extracted_content.get(section, {})
                story.append(PageBreak())
                story.append(Paragraph(section, self.styles['SectionHeading']))
                story.append(Spacer(1, 0.1 * inch))

                # Add text-based content for the section
                text_content = content.get("text", []) if isinstance(content, dict) else [str(content)]
                if text_content:
                    full_text = "\n\n".join(text_content)
                    story.append(Paragraph(self._clean_text(full_text), self.styles['CustomBody']))
                else:
                    story.append(Paragraph("No textual information was extracted for this section.", self.styles['CustomBody']))

                # Note about images if they exist
                if isinstance(content, dict) and "images" in content and content["images"]:
                    story.append(Spacer(1, 0.2 * inch))
                    story.append(Paragraph(
                        f"<i>Note: {len(content['images'])} image(s) related to this section were detected in the source documents.</i>",
                        self.styles['CustomBody']
                    ))

            # === 5. Build the PDF ===
            doc.build(story, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
            
            logger.info(f"Report assembled successfully: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error during report assembly: {e}", exc_info=True)
            raise