"""
PDF Report Generation - US-2.5
Generate professional PDF reports for stakeholder communication
"""

from typing import Dict, List, Optional, BinaryIO
from datetime import datetime, timezone
from io import BytesIO
import logging

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image as RLImage
    )
    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)


class ReportService:
    """Service for PDF report generation (US-2.5)"""
    
    @staticmethod
    async def generate_emissions_report(
        org_name: str,
        total_emissions: float,
        scope_breakdown: Dict[int, float],
        monthly_trend: List[Dict],
        category_breakdown: List[Dict],
        date_range: str = "All Time"
    ) -> BytesIO:
        """
        Generate professional PDF report
        
        AC:
        - PDF generates in under 3 seconds
        - All charts render correctly
        - File size under 5 MB
        - Includes all required sections
        
        Returns:
            BytesIO buffer containing PDF
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF generation")
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Title
        elements.append(Paragraph(
            f"Carbon Emissions Report<br/>{org_name}",
            title_style
        ))
        elements.append(Spacer(1, 12))
        
        # Metadata
        meta_data = [
            ['Report Generated:', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')],
            ['Period:', date_range],
            ['Total Emissions:', f"{total_emissions:.3f} tonnes CO2e"]
        ]
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 20))
        
        # Scope Breakdown Section
        elements.append(Paragraph("Emissions by Scope", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        # Scope breakdown table
        scope_data = [['Scope', 'Emissions (tonnes CO2e)', 'Percentage']]
        for scope in [1, 2, 3]:
            emissions = scope_breakdown.get(scope, 0.0)
            percentage = (emissions / total_emissions * 100) if total_emissions > 0 else 0
            scope_data.append([
                f"Scope {scope}",
                f"{emissions:.3f}",
                f"{percentage:.1f}%"
            ])
        
        scope_table = Table(scope_data, colWidths=[1.5*inch, 2*inch, 1.5*inch])
        scope_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(scope_table)
        elements.append(Spacer(1, 20))
        
        # Pie Chart
        if total_emissions > 0:
            drawing = Drawing(400, 200)
            pie = Pie()
            pie.x = 150
            pie.y = 50
            pie.width = 100
            pie.height = 100
            pie.data = [scope_breakdown.get(i, 0.0) for i in [1, 2, 3]]
            pie.labels = [f"Scope {i}" for i in [1, 2, 3]]
            pie.slices.strokeWidth = 0.5
            drawing.add(pie)
            elements.append(drawing)
            elements.append(Spacer(1, 20))
        
        # Category Breakdown
        elements.append(Paragraph("Top Emission Categories", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        if category_breakdown:
            cat_data = [['Category', 'Emissions (tonnes CO2e)']]
            for cat in category_breakdown[:10]:
                cat_data.append([
                    cat['category'],
                    f"{cat['emissions_tonnes']:.3f}"
                ])
            
            cat_table = Table(cat_data, colWidths=[3*inch, 2*inch])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(cat_table)
        
        elements.append(Spacer(1, 20))
        
        # Footer
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Report generated by Carbon Accounting Platform v1.0<br/>"
            f"© {datetime.now().year} | GHG Protocol Compliant",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        logger.info(f"Generated PDF report: {len(buffer.getvalue())} bytes")
        return buffer