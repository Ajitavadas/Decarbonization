"""
Professional Carbon Footprint Report Generator
Generates comprehensive reports with visualizations matching industry standards
"""

import io
from datetime import datetime
from typing import Dict, List, Any, Optional
from decimal import Decimal

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.activity import EmissionActivity
from app.models.organization import Organization


class ReportGenerator:
    """Generate professional carbon footprint reports"""
    
    def __init__(self, db: Session, project_id: str, output_format: str = 'pdf'):
        self.db = db
        self.project_id = project_id
        self.output_format = output_format
        self.project_data = None
        self.activities = []
        self.summary = {}
        
    def generate(self) -> io.BytesIO:
        """Main entry point for report generation"""
        # Fetch data
        self._fetch_data()
        
        # Calculate summary statistics
        self._calculate_summary()
        
        # Generate visualizations
        viz_buffer = self._generate_visualizations()
        
        # Generate report based on format
        if self.output_format == 'pdf':
            return self._generate_pdf(viz_buffer)
        elif self.output_format == 'html':
            return self._generate_html(viz_buffer)
        else:
            raise ValueError(f"Unsupported format: {self.output_format}")
    
    def _fetch_data(self):
        """Fetch project and activities from database"""
        # Get project with organization
        project = self.db.query(Project).filter(
            Project.id == self.project_id
        ).first()
        
        if not project:
            raise ValueError(f"Project {self.project_id} not found")
        
        # Get organization
        org = self.db.query(Organization).filter(
            Organization.id == project.organization_id
        ).first()
        
        # Get activities
        activities = self.db.query(EmissionActivity).filter(
            EmissionActivity.project_id == self.project_id
        ).order_by(EmissionActivity.created_at).all()
        
        self.project_data = {
            'id': str(project.id),
            'name': project.name,
            'description': project.description,
            'organization': org.name if org else 'N/A',
            'start_date': str(project.start_date) if project.start_date else 'N/A',
            'end_date': str(project.end_date) if project.end_date else 'N/A',
            'reporting_year': str(project.reporting_year) if project.reporting_year else 'N/A',
            'created_at': project.created_at
        }
        
        self.activities = [
            {
                'id': str(act.id),
                'type': act.activity_type or 'N/A',
                'scope': act.scope or 'Unknown',
                'co2e_kg': float(act.co2e_kg) if act.co2e_kg else 0.0,
                'region': act.region or 'N/A',
                'date': str(act.activity_date) if act.activity_date else 'N/A',
                'emission_factor_id': act.emission_factor_id or 'N/A',
                'calculation_method': act.calculation_method or 'N/A',
                'source_dataset': act.source_dataset or 'N/A',
                'input_data': act.input_data if hasattr(act, 'input_data') and act.input_data else {},
                'description': act.input_data.get('description', 'N/A') if hasattr(act, 'input_data') and act.input_data else 'N/A'
            }
            for act in activities
        ]
    
    def _calculate_summary(self):
        """Calculate summary statistics"""
        total_co2e = sum(a['co2e_kg'] for a in self.activities)
        
        # Scope breakdown
        scope_breakdown = {}
        for activity in self.activities:
            scope = activity['scope']
            scope_breakdown[scope] = scope_breakdown.get(scope, 0) + activity['co2e_kg']
        
        # Activity type breakdown
        activity_breakdown = {}
        for activity in self.activities:
            act_type = activity['type']
            activity_breakdown[act_type] = activity_breakdown.get(act_type, 0) + activity['co2e_kg']
        
        # Top 5 activities
        top_activities = sorted(self.activities, key=lambda x: x['co2e_kg'], reverse=True)[:5]
        
        # Scope percentages
        scope_percentages = {}
        if total_co2e > 0:
            for scope, value in scope_breakdown.items():
                scope_percentages[scope] = (value / total_co2e) * 100
        
        self.summary = {
            'total_co2e_kg': total_co2e,
            'total_activities': len(self.activities),
            'scope_breakdown': scope_breakdown,
            'scope_percentages': scope_percentages,
            'activity_breakdown': activity_breakdown,
            'top_activities': top_activities
        }
    
    def _generate_visualizations(self) -> io.BytesIO:
        """Generate all charts and return as BytesIO buffer"""
        # Restructured layout: 2x2 grid with 4 charts (removed scope contribution chart)
        fig = plt.figure(figsize=(14, 10))
        gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)
        
        # Color scheme matching professional reports
        colors_scope = ['#FF6B6B', '#4ECDC4', '#45B7D1']  # Red, Teal, Blue
        
        # 1. Scope Pie Chart (Top Left)
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_scope_pie(ax1, colors_scope)
        
        # 2. Activity Type Bar Chart (Top Right)
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_activity_breakdown(ax2)
        
        # 3. Top 5 Emission Hotspots (Bottom Left)
        ax3 = fig.add_subplot(gs[1, 0])
        self._plot_top_activities(ax3)
        
        # 4. Monthly Trend (Bottom Right)
        ax4 = fig.add_subplot(gs[1, 1])
        self._plot_monthly_trend(ax4)
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buffer.seek(0)
        return buffer
    
    def _plot_scope_pie(self, ax, colors):
        """Plot scope breakdown pie chart"""
        scope_data = self.summary['scope_breakdown']
        if not scope_data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax.axis('off')
            return
        
        labels = list(scope_data.keys())
        sizes = list(scope_data.values())
        
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            colors=colors[:len(labels)], startangle=90,
            textprops={'fontsize': 10, 'weight': 'bold'}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
        
        ax.set_title('GHG Emissions by Scope', fontsize=12, weight='bold', pad=15)
    
    def _plot_activity_breakdown(self, ax):
        """Plot activity type breakdown as horizontal bar"""
        activity_data = self.summary['activity_breakdown']
        if not activity_data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax.axis('off')
            return
        
        # Sort by value
        sorted_items = sorted(activity_data.items(), key=lambda x: x[1], reverse=True)
        activities = [item[0].replace('_', ' ').title() for item in sorted_items]
        values = [item[1] for item in sorted_items]
        
        y_pos = np.arange(len(activities))
        bars = ax.barh(y_pos, values, color='#4ECDC4', edgecolor='black', linewidth=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(activities, fontsize=9)
        ax.set_xlabel('CO2e (kg)', fontsize=10, weight='bold')
        ax.set_title('Emissions by Activity Type', fontsize=12, weight='bold', pad=15)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, values)):
            ax.text(value + max(values) * 0.02, i, f'{value:,.1f}',
                   va='center', fontsize=8, weight='bold')
    
    def _plot_top_activities(self, ax):
        """Plot top 5 emission hotspots"""
        top_acts = self.summary['top_activities']
        if not top_acts:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax.axis('off')
            return
        
        labels = [f"{a['type'][:15]}..." if len(a['type']) > 15 else a['type'] 
                 for a in top_acts]
        values = [a['co2e_kg'] for a in top_acts]
        
        y_pos = np.arange(len(labels))
        bars = ax.barh(y_pos, values, color='#FF6B6B', edgecolor='black', linewidth=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel('CO2e (kg)', fontsize=10, weight='bold')
        ax.set_title('Top 5 Emission Hotspots', fontsize=12, weight='bold', pad=15)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, values)):
            ax.text(value + max(values) * 0.02, i, f'{value:,.1f}',
                   va='center', fontsize=8, weight='bold')
    
    def _plot_scope_contribution(self, ax, colors):
        """Plot scope contribution as stacked horizontal bar"""
        scope_data = self.summary['scope_breakdown']
        if not scope_data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax.axis('off')
            return
        
        scopes = list(scope_data.keys())
        values = list(scope_data.values())
        
        left = 0
        for i, (scope, value) in enumerate(zip(scopes, values)):
            ax.barh(0, value, left=left, height=0.5, 
                   label=scope, color=colors[i % len(colors)],
                   edgecolor='black', linewidth=1)
            # Add label in the middle of each segment
            if value > max(values) * 0.05:  # Only show label if segment is large enough
                ax.text(left + value/2, 0, f'{value:,.0f} kg',
                       ha='center', va='center', fontsize=9, weight='bold', color='white')
            left += value
        
        ax.set_ylim(-0.5, 0.5)
        ax.set_xlim(0, sum(values))
        ax.set_yticks([])
        ax.set_xlabel('Total CO2e (kg)', fontsize=10, weight='bold')
        ax.set_title('Scope Contribution Breakdown', fontsize=12, weight='bold', pad=15)
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    def _plot_monthly_trend(self, ax):
        """Plot monthly emissions trend if dates available"""
        # Group by month if date data exists
        try:
            monthly_data = {}
            for activity in self.activities:
                if activity['date'] != 'N/A':
                    date_str = activity['date'][:7]  # YYYY-MM
                    monthly_data[date_str] = monthly_data.get(date_str, 0) + activity['co2e_kg']
            
            if monthly_data:
                months = sorted(monthly_data.keys())
                values = [monthly_data[m] for m in months]
                
                x_pos = np.arange(len(months))
                ax.plot(x_pos, values, marker='o', linewidth=2, 
                       markersize=8, color='#45B7D1', markerfacecolor='#FF6B6B')
                ax.fill_between(x_pos, values, alpha=0.3, color='#45B7D1')
                
                ax.set_xticks(x_pos)
                ax.set_xticklabels([m[5:7] + '/' + m[2:4] for m in months], 
                                  rotation=45, ha='right', fontsize=8)
                ax.set_ylabel('CO2e (kg)', fontsize=10, weight='bold')
                ax.set_title('Monthly Emissions Trend', fontsize=12, weight='bold', pad=15)
                ax.grid(True, alpha=0.3, linestyle='--')
            else:
                ax.text(0.5, 0.5, 'Insufficient Date Data', ha='center', va='center')
                ax.axis('off')
        except Exception:
            ax.text(0.5, 0.5, 'Unable to Generate Trend', ha='center', va='center')
            ax.axis('off')
    
    def _plot_summary_box(self, ax):
        """Display key summary statistics"""
        ax.axis('off')
        
        # Title
        ax.text(0.5, 0.95, 'Summary Statistics', 
               ha='center', va='top', fontsize=14, weight='bold')
        
        # Stats
        stats = [
            ('Total Activities', self.summary['total_activities']),
            ('Total CO2e', f"{self.summary['total_co2e_kg']:,.2f} kg"),
            ('', ''),  # Spacer
            ('Scope 1 (Direct)', f"{self.summary['scope_breakdown'].get('Scope 1', 0):,.1f} kg"),
            ('Scope 2 (Indirect)', f"{self.summary['scope_breakdown'].get('Scope 2', 0):,.1f} kg"),
            ('Scope 3 (Value Chain)', f"{self.summary['scope_breakdown'].get('Scope 3', 0):,.1f} kg"),
        ]
        
        y_pos = 0.80
        for label, value in stats:
            if label:  # Skip spacers
                ax.text(0.05, y_pos, label, ha='left', va='top', fontsize=10, weight='bold')
                ax.text(0.95, y_pos, str(value), ha='right', va='top', fontsize=10)
            y_pos -= 0.12
        
        # Add box
        rect = mpatches.FancyBboxPatch((0, 0), 1, 1, 
                                       boxstyle="round,pad=0.02",
                                       edgecolor='black', facecolor='#f0f0f0',
                                       linewidth=2, transform=ax.transAxes)
        ax.add_patch(rect)
    
    def _generate_pdf(self, viz_buffer: io.BytesIO) -> io.BytesIO:
        """Generate PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=30, leftMargin=30,
                              topMargin=30, bottomMargin=30)
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Title
        title = Paragraph("Carbon Footprint Report", title_style)
        elements.append(title)
        
        # Project info
        project_info = [
            f"<b>Organization:</b> {self.project_data['organization']}",
            f"<b>Project:</b> {self.project_data['name']}",
            f"<b>Reporting Period:</b> {self.project_data['start_date']} to {self.project_data['end_date']}",
            f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        for info in project_info:
            elements.append(Paragraph(info, styles['Normal']))
        
        elements.append(Spacer(1, 20))
        
        # Executive Summary
        elements.append(Paragraph("Executive Summary", heading_style))
        
        summary_text = f"""
        This report presents a comprehensive analysis of greenhouse gas emissions for 
        {self.project_data['organization']}. During the reporting period, a total of 
        <b>{self.summary['total_activities']}</b> emission activities were recorded, 
        resulting in <b>{self.summary['total_co2e_kg']:,.2f} kg CO2e</b> of total emissions.
        """
        elements.append(Paragraph(summary_text, styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Visualizations
        elements.append(Paragraph("Emissions Analysis & Visualizations", heading_style))
        
        # Add charts
        img = Image(viz_buffer, width=7*inch, height=5.25*inch)
        elements.append(img)
        elements.append(PageBreak())
        
        # Summary Table
        elements.append(Paragraph("Summary Totals", heading_style))
        
        summary_data = [
            ['Scope', 'CO2e (kg)', '%', 'Activities'],
        ]
        
        for scope in ['Scope 1', 'Scope 2', 'Scope 3']:
            value = self.summary['scope_breakdown'].get(scope, 0)
            percentage = self.summary['scope_percentages'].get(scope, 0)
            count = len([a for a in self.activities if a['scope'] == scope])
            summary_data.append([
                scope,
                f"{value:,.2f}",
                f"{percentage:.1f}%",
                str(count)
            ])
        
        # Add total row
        summary_data.append([
            'Total',
            f"{self.summary['total_co2e_kg']:,.2f}",
            '100%',
            str(self.summary['total_activities'])
        ])
        
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch, 1.5*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ECF0F1')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Activity Type Breakdown
        elements.append(Paragraph("Activity Type Breakdown", heading_style))
        
        activity_data = [['Activity Type', 'CO2e (kg)', 'Count']]
        for act_type, value in sorted(self.summary['activity_breakdown'].items(), 
                                     key=lambda x: x[1], reverse=True):
            count = len([a for a in self.activities if a['type'] == act_type])
            activity_data.append([
                act_type.replace('_', ' ').title(),
                f"{value:,.2f}",
                str(count)
            ])
        
        activity_table = Table(activity_data, colWidths=[3*inch, 2*inch, 2*inch])
        activity_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(activity_table)
        elements.append(PageBreak())
        
        # Detailed Activities Table
        elements.append(Paragraph("Detailed Activity List", heading_style))
        
        detailed_data = [['#', 'Type', 'Scope', 'Quantity', 'Unit', 'CO2e (kg)', 'Calc Method', 'Emission Factor', 'Region', 'Date']]
        for i, activity in enumerate(self.activities, 1):
            # Extract quantity and unit from input_data
            input_data = activity.get('input_data', {})
            quantity = 'N/A'
            unit = 'N/A'
            
            # Try different possible field names in input_data
            if isinstance(input_data, dict):
                # Check for common quantity fields
                for qty_field in ['energy', 'volume', 'weight', 'distance', 'money', 'amount']:
                    if qty_field in input_data:
                        quantity = f"{input_data[qty_field]:,.2f}"
                        break
                
                # Check for common unit fields
                for unit_field in ['energy_unit', 'volume_unit', 'weight_unit', 'distance_unit', 'money_unit', 'unit']:
                    if unit_field in input_data:
                        unit = input_data[unit_field]
                        break
            
            detailed_data.append([
                str(i),
                activity['type'][:15],
                activity['scope'],
                quantity,
                unit,
                f"{activity['co2e_kg']:,.2f}",
                activity.get('calculation_method', 'N/A')[:12],
                activity.get('emission_factor_id', 'N/A')[:25] + '...' if activity.get('emission_factor_id', 'N/A') != 'N/A' and len(activity.get('emission_factor_id', '')) > 25 else activity.get('emission_factor_id', 'N/A'),
                activity['region'],
                activity['date'][:10] if activity['date'] != 'N/A' else 'N/A'
            ])
        
        detailed_table = Table(detailed_data, 
                              colWidths=[0.3*inch, 1.1*inch, 0.7*inch, 0.7*inch, 0.5*inch, 0.8*inch, 0.8*inch, 1.5*inch, 0.5*inch, 0.8*inch])
        detailed_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))
        
        elements.append(detailed_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def _generate_html(self, viz_buffer: io.BytesIO) -> str:
        """Generate HTML report"""
        import base64
        
        # Convert image to base64
        viz_base64 = base64.b64encode(viz_buffer.read()).decode('utf-8')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Carbon Footprint Report</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f5f5f5;
                    padding: 20px;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2C3E50;
                    text-align: center;
                    margin-bottom: 10px;
                    font-size: 32px;
                }}
                .subtitle {{
                    text-align: center;
                    color: #34495E;
                    font-size: 18px;
                    margin-bottom: 5px;
                }}
                .report-date {{
                    text-align: center;
                    color: #7F8C8D;
                    font-size: 14px;
                    margin-bottom: 30px;
                }}
                h2 {{
                    color: #2C3E50;
                    border-bottom: 3px solid #3498DB;
                    padding-bottom: 10px;
                    margin-top: 30px;
                    margin-bottom: 15px;
                    font-size: 20px;
                }}
                .summary-box {{
                    background: linear-gradient(135deg, #667EEA 0%, #764BA2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-size: 16px;
                }}
                .summary-item {{
                    margin: 10px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th {{
                    background-color: #3498DB;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                }}
                td {{
                    padding: 10px 12px;
                    border-bottom: 1px solid #ddd;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .visualization {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .visualization img {{
                    max-width: 100%;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .scope-1 {{ color: #FF6B6B; font-weight: bold; }}
                .scope-2 {{ color: #4ECDC4; font-weight: bold; }}
                .scope-3 {{ color: #FFD93D; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Carbon Footprint Report</h1>
                <div class="subtitle">{self.project_data['organization']} - {self.project_data['name']}</div>
                <div class="subtitle">Reporting Period: {self.project_data['start_date']} to {self.project_data['end_date']}</div>
                <div class="report-date">Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                
                <h2>Executive Summary</h2>
                <div class="summary-box">
                    <div class="summary-item"><strong>Total Activities:</strong> {self.summary['total_activities']}</div>
                    <div class="summary-item"><strong>Total CO2e:</strong> {self.summary['total_co2e_kg']:,.2f} kg</div>
                    <div class="summary-item"><strong>Reporting Year:</strong> {self.project_data['reporting_year']}</div>
                </div>
                
                <h2>Visualizations</h2>
                <div class="visualization">
                    <img src="data:image/png;base64,{viz_base64}" alt="Emissions Charts">
                </div>
                
                <h2>Scope Breakdown</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Scope</th>
                            <th>CO2e (kg)</th>
                            <th>Percentage</th>
                            <th>Activity Count</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for scope in ['Scope 1', 'Scope 2', 'Scope 3']:
            value = self.summary['scope_breakdown'].get(scope, 0)
            percentage = self.summary['scope_percentages'].get(scope, 0)
            count = len([a for a in self.activities if a['scope'] == scope])
            html += f"""
                        <tr>
                            <td class="scope-{scope.split()[1].lower()}">{scope}</td>
                            <td>{value:,.2f}</td>
                            <td>{percentage:.1f}%</td>
                            <td>{count}</td>
                        </tr>
            """
        
        html += f"""
                        <tr style="background-color: #ECF0F1; font-weight: bold;">
                            <td>Total</td>
                            <td>{self.summary['total_co2e_kg']:,.2f}</td>
                            <td>100%</td>
                            <td>{self.summary['total_activities']}</td>
                        </tr>
                    </tbody>
                </table>
                
                <h2>Activity Type Breakdown</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Activity Type</th>
                            <th>CO2e (kg)</th>
                            <th>Count</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for act_type, value in sorted(self.summary['activity_breakdown'].items(), 
                                     key=lambda x: x[1], reverse=True):
            count = len([a for a in self.activities if a['type'] == act_type])
            html += f"""
                        <tr>
                            <td>{act_type.replace('_', ' ').title()}</td>
                            <td>{value:,.2f}</td>
                            <td>{count}</td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
                
                <h2>Detailed Activity List</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Type</th>
                            <th>Scope</th>
                            <th>Quantity</th>
                            <th>Unit</th>
                            <th>CO2e (kg)</th>
                            <th>Calculation Method</th>
                            <th>Emission Factor</th>
                            <th>Region</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for i, activity in enumerate(self.activities, 1):
            # Extract quantity and unit from input_data
            input_data = activity.get('input_data', {})
            quantity = 'N/A'
            unit = 'N/A'
            
            if isinstance(input_data, dict):
                # Check for common quantity fields
                for qty_field in ['energy', 'volume', 'weight', 'distance', 'money', 'amount']:
                    if qty_field in input_data:
                        quantity = f"{input_data[qty_field]:,.2f}"
                        break
                
                # Check for common unit fields
                for unit_field in ['energy_unit', 'volume_unit', 'weight_unit', 'distance_unit', 'money_unit', 'unit']:
                    if unit_field in input_data:
                        unit = input_data[unit_field]
                        break
            
            emission_factor = activity.get('emission_factor_id', 'N/A')
            if emission_factor != 'N/A' and len(emission_factor) > 40:
                emission_factor = emission_factor[:40] + '...'
            
            html += f"""
                        <tr>
                            <td>{i}</td>
                            <td>{activity['type']}</td>
                            <td class="scope-{activity['scope'].split()[1].lower() if 'Scope' in activity['scope'] else '1'}">{activity['scope']}</td>
                            <td>{quantity}</td>
                            <td>{unit}</td>
                            <td>{activity['co2e_kg']:,.2f}</td>
                            <td>{activity.get('calculation_method', 'N/A')}</td>
                            <td style="font-size: 9px;">{emission_factor}</td>
                            <td>{activity['region']}</td>
                            <td>{activity['date'][:10] if activity['date'] != 'N/A' else 'N/A'}</td>
                        </tr>
            """
        
        html += """
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        
        return html
