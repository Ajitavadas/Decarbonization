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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas

from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.activity import EmissionActivity
from app.models.organization import Organization


class ReportGenerator:
    """Generate professional carbon footprint reports"""
    
    def __init__(self, db: Session, project_id: str):
        self.db = db
        self.project_id = project_id
        self.project_data = None
        self.activities = []
        self.summary = {}
        
    def generate(self) -> io.BytesIO:
        """Main entry point for PDF report generation"""
        # Fetch data
        self._fetch_data()
        
        # Calculate summary statistics
        self._calculate_summary()
        
        # Generate visualizations
        viz_buffer = self._generate_visualizations()
        
        # Generate PDF report
        return self._generate_pdf(viz_buffer)
    
    def generate_custom(self, config: Dict[str, Any]) -> io.BytesIO:
        """Generate custom PDF report based on user configuration"""
        # Fetch data
        self._fetch_data()
        
        # Calculate summary statistics
        self._calculate_summary()
        
        # Generate visualizations if requested
        viz_buffer = None
        if config.get('include_charts', True):
            viz_buffer = self._generate_visualizations()
        
        # Generate custom PDF report
        return self._generate_custom_pdf(config, viz_buffer)
    
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

    def _scope_sort_key(self, scope: str) -> int:
        """Return numeric scope ordering for consistent table sorting"""
        try:
            return int(''.join(ch for ch in str(scope) if ch.isdigit()))
        except Exception:
            return 99

    def _extract_quantity_unit(self, activity: Dict[str, Any]) -> tuple[Optional[float], str]:
        """Extract quantity and unit from Climatiq autopilot_response in input_data"""
        quantity: Optional[float] = None
        unit = 'N/A'
        input_data = activity.get('input_data', {}) if isinstance(activity.get('input_data', {}), dict) else {}

        # Priority 1: Check direct fields in input_data (from CSV upload)
        for qty_field in ['amount', 'quantity', 'value']:
            if qty_field in input_data and input_data[qty_field] is not None:
                try:
                    quantity = float(input_data[qty_field])
                    break
                except (TypeError, ValueError):
                    continue

        for unit_field in ['unit']:
            if unit_field in input_data and input_data[unit_field]:
                unit = str(input_data[unit_field])
                break

        # Priority 2: Extract from autopilot_response (Climatiq data)
        autopilot = input_data.get('autopilot_response', {}) if isinstance(input_data.get('autopilot_response', {}), dict) else {}
        if autopilot:
            estimate = autopilot.get('estimate', {}) if isinstance(autopilot.get('estimate', {}), dict) else {}
            
            # Climatiq returns the input parameters in the estimate
            if not quantity and estimate:
                # Check common Climatiq parameter fields
                for qty_field in ['energy', 'volume', 'weight', 'distance', 'money', 'amount', 'value']:
                    if qty_field in estimate and estimate[qty_field] is not None:
                        try:
                            quantity = float(estimate[qty_field])
                            break
                        except (TypeError, ValueError):
                            continue
            
            if unit == 'N/A' and estimate:
                # Check Climatiq unit fields
                for unit_field in ['energy_unit', 'volume_unit', 'weight_unit', 'distance_unit', 'money_unit', 'unit']:
                    if unit_field in estimate and estimate[unit_field]:
                        unit = str(estimate[unit_field])
                        break

        return quantity, unit

    def _extract_emission_source(self, activity: Dict[str, Any]) -> tuple[str, str]:
        """Extract emission source from CSV description and data source from Climatiq"""
        input_data = activity.get('input_data', {}) if isinstance(activity.get('input_data', {}), dict) else {}
        source_name: Optional[str] = None
        data_source: Optional[str] = None
        
        # Priority 1: Use description from CSV input (user's activity description)
        desc = input_data.get('description', '')
        if desc and desc not in ['N/A', None, '']:
            source_name = desc
        
        # Priority 2: Fall back to activity description field
        if not source_name:
            desc = activity.get('description', '')
            if desc and desc not in ['N/A', None, '']:
                source_name = desc
        
        # Priority 3: Use Climatiq emission factor name
        if not source_name:
            autopilot = input_data.get('autopilot_response', {}) if isinstance(input_data.get('autopilot_response', {}), dict) else {}
            if autopilot:
                ef = autopilot.get('emission_factor') or autopilot.get('emissionFactor')
                if isinstance(ef, dict):
                    source_name = ef.get('name') or ef.get('activity_id') or ef.get('id')
                
                estimate = autopilot.get('estimate', {}) if isinstance(autopilot.get('estimate', {}), dict) else {}
                if not source_name and estimate:
                    ef_details = estimate.get('emission_factor') or estimate.get('emissionFactor')
                    if isinstance(ef_details, dict):
                        source_name = ef_details.get('name') or ef_details.get('activity_id')
        
        # Priority 4: Use database fields or activity type
        if not source_name:
            source_name = activity.get('emission_factor_id') or activity.get('type', 'Unknown Activity')
        
        # Get data source from Climatiq metadata
        autopilot = input_data.get('autopilot_response', {}) if isinstance(input_data.get('autopilot_response', {}), dict) else {}
        if autopilot:
            ef = autopilot.get('emission_factor') or autopilot.get('emissionFactor')
            if isinstance(ef, dict):
                data_source = ef.get('source') or ef.get('source_dataset') or ef.get('data_version')
            
            if not data_source:
                estimate = autopilot.get('estimate', {}) if isinstance(autopilot.get('estimate', {}), dict) else {}
                ef_details = estimate.get('emission_factor') if estimate else None
                if isinstance(ef_details, dict):
                    data_source = ef_details.get('source') or ef_details.get('source_dataset')
        
        if not data_source:
            data_source = activity.get('source_dataset') or 'Climatiq API'

        return source_name or 'Unknown', data_source

    def _build_activity_summary_rows(self) -> List[List[str]]:
        """Prepare rows for activity data summary grouped by scope"""
        rows: List[List[str]] = [['Activity Type', 'Emission Source', 'Activity Data', 'Unit', 'Scope']]
        sorted_activities = sorted(self.activities, key=lambda a: (self._scope_sort_key(a.get('scope', '')), -a.get('co2e_kg', 0)))

        for activity in sorted_activities:
            quantity, unit = self._extract_quantity_unit(activity)
            source_name, _ = self._extract_emission_source(activity)
            activity_label = (activity.get('type') or 'Unknown').replace('_', ' ').title()
            rows.append([
                activity_label,
                source_name,
                f"{quantity:,.2f}" if quantity is not None else 'N/A',
                unit,
                activity.get('scope', 'Unknown')
            ])

        return rows

    def _build_emission_factor_rows(self) -> List[List[str]]:
        """Prepare emission factor table with actual EF values from Climatiq when available"""
        aggregated: Dict[tuple, Dict[str, Any]] = {}

        for activity in self.activities:
            quantity, unit = self._extract_quantity_unit(activity)
            if not quantity or quantity == 0:
                continue

            key_source, data_source = self._extract_emission_source(activity)
            
            # Try to get actual emission factor from Climatiq response
            input_data = activity.get('input_data', {}) if isinstance(activity.get('input_data', {}), dict) else {}
            autopilot = input_data.get('autopilot_response', {}) if isinstance(input_data.get('autopilot_response', {}), dict) else {}
            ef_value = None
            
            if autopilot:
                # Check emission_factor object for factor value
                ef_obj = autopilot.get('emission_factor') or autopilot.get('emissionFactor')
                if isinstance(ef_obj, dict):
                    # Climatiq returns 'factor' or 'co2e_factor' fields
                    ef_value = ef_obj.get('factor') or ef_obj.get('co2e_factor') or ef_obj.get('co2eFactor')
                
                # Also check in estimate
                if not ef_value:
                    estimate = autopilot.get('estimate', {}) if isinstance(autopilot.get('estimate', {}), dict) else {}
                    ef_details = estimate.get('emission_factor')
                    if isinstance(ef_details, dict):
                        ef_value = ef_details.get('factor') or ef_details.get('co2e_factor')
            
            key = (activity.get('scope', 'Unknown'), key_source, unit)
            entry = aggregated.setdefault(key, {
                'co2e': 0.0, 
                'quantity': 0.0, 
                'data_source': data_source,
                'ef_value': ef_value,
                'count': 0
            })
            entry['co2e'] += float(activity.get('co2e_kg', 0) or 0)
            entry['quantity'] += float(quantity)
            entry['count'] += 1
            if not entry.get('data_source') and data_source:
                entry['data_source'] = data_source
            # Keep the emission factor if found
            if not entry.get('ef_value') and ef_value:
                entry['ef_value'] = ef_value

        rows: List[List[str]] = [['Scope', 'Emission Source', 'Unit', 'kgCO2e per Unit', 'Data Source']]
        for (scope, source_name, unit), payload in sorted(aggregated.items(), key=lambda k: self._scope_sort_key(k[0][0])):
            # Calculate emission factor: EF = CO2e / Quantity
            if payload['quantity'] > 0:
                factor = payload['co2e'] / payload['quantity']
                factor_display = f"{factor:.6f}"
            else:
                factor_display = 'N/A'
            
            rows.append([
                scope,
                source_name,
                unit or 'N/A',
                factor_display,
                payload.get('data_source') or 'Climatiq API'
            ])

        return rows

    def _build_gas_summary_rows(self) -> List[List[str]]:
        """Prepare base-year style GHG summary with constituent gas breakdown from Climatiq"""
        grouped: Dict[tuple, Dict[str, float]] = {}

        for activity in self.activities:
            # Use emission source as label instead of generic type
            source_label, _ = self._extract_emission_source(activity)
            key = (activity.get('scope', 'Unknown'), source_label)
            bucket = grouped.setdefault(key, {'co2e': 0.0, 'co2': 0.0, 'ch4': 0.0, 'n2o': 0.0, 'other': 0.0, 'has_gas_split': False})

            bucket['co2e'] += float(activity.get('co2e_kg', 0) or 0)

            # Extract constituent gases from multiple possible locations
            input_data = activity.get('input_data', {}) if isinstance(activity.get('input_data', {}), dict) else {}
            autopilot = input_data.get('autopilot_response', {}) if isinstance(input_data.get('autopilot_response', {}), dict) else {}
            
            # Try database field first
            gas_breakdown = activity.get('constituent_gases')
            
            # Then try autopilot response
            if not gas_breakdown and autopilot:
                gas_breakdown = autopilot.get('constituent_gases') or autopilot.get('constituentGases')
                
                # Also check estimate object
                estimate = autopilot.get('estimate', {}) if isinstance(autopilot.get('estimate', {}), dict) else {}
                if not gas_breakdown and estimate:
                    gas_breakdown = estimate.get('constituent_gases') or estimate.get('constituentGases')

            if isinstance(gas_breakdown, dict) and gas_breakdown:
                bucket['has_gas_split'] = True
                # Extract individual gases (Climatiq returns in kg CO2e already)
                bucket['co2'] += float(gas_breakdown.get('co2', 0) or 0)
                bucket['ch4'] += float(gas_breakdown.get('ch4', 0) or 0)
                bucket['n2o'] += float(gas_breakdown.get('n2o', 0) or 0)
                
                # Capture other GHGs (HFCs, PFCs, SF6, etc.)
                for gas_key, gas_val in gas_breakdown.items():
                    if gas_key.lower() not in ['co2', 'co2e', 'ch4', 'n2o']:
                        try:
                            bucket['other'] += float(gas_val)
                        except (TypeError, ValueError):
                            continue

        rows: List[List[str]] = [['Scope', 'Emission Source', 'CO2e (kg)', 'CO2 (kg)', 'CH4 (kg)', 'N2O (kg)', 'Other GHGs (kg)']]
        for (scope, source_label), payload in sorted(grouped.items(), key=lambda item: (self._scope_sort_key(item[0][0]), -item[1]['co2e'])):
            rows.append([
                scope,
                source_label,
                f"{payload['co2e']:,.2f}",
                f"{payload['co2']:,.3f}" if payload['has_gas_split'] else 'N/A',
                f"{payload['ch4']:,.3f}" if payload['has_gas_split'] else 'N/A',
                f"{payload['n2o']:,.3f}" if payload['has_gas_split'] else 'N/A',
                f"{payload['other']:,.3f}" if payload['has_gas_split'] and payload['other'] > 0 else 'N/A'
            ])

        return rows
    
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

        # Summary Totals (kept inside Executive Summary section)
        summary_heading = Paragraph("Summary Totals", heading_style)
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

        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch, 1.5*inch, 1.5*inch], repeatRows=1)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7FA87F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))

        elements.append(KeepTogether([summary_heading, summary_table, Spacer(1, 20)]))
        
        # Visualizations
        elements.append(Paragraph("Emissions Analysis & Visualizations", heading_style))
        
        # Add charts
        img = Image(viz_buffer, width=7*inch, height=5.25*inch)
        elements.append(img)
        elements.append(PageBreak())
        
        # Activity Data by Scope
        activity_heading = Paragraph("Activity Data by Scope", heading_style)
        activity_rows = self._build_activity_summary_rows()
        activity_table = Table(activity_rows, colWidths=[2.2*inch, 2.2*inch, 1.2*inch, 0.8*inch, 0.9*inch], repeatRows=1)
        activity_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7FA87F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))
        elements.append(KeepTogether([activity_heading, activity_table, Spacer(1, 16)]))

        # Emission Factors Used (derived when missing in DB)
        ef_heading = Paragraph("Emission Factors Used", heading_style)
        ef_rows = self._build_emission_factor_rows()
        emission_table = Table(ef_rows, colWidths=[1.0*inch, 2.4*inch, 0.9*inch, 1.0*inch, 2.0*inch], repeatRows=1)
        emission_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7FA87F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))
        elements.append(KeepTogether([ef_heading, emission_table]))
        elements.append(PageBreak())

        # GHG Emissions Summary (Base-Year style)
        gas_heading = Paragraph("GHG Emissions by Scope and Gas", heading_style)
        gas_rows = self._build_gas_summary_rows()
        gas_table = Table(gas_rows, colWidths=[0.8*inch, 2.0*inch, 0.9*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.0*inch], repeatRows=1)
        gas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7FA87F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))
        elements.append(KeepTogether([gas_heading, gas_table]))
        elements.append(PageBreak())
        
        # Activity Type Breakdown
        type_heading = Paragraph("Activity Type Breakdown", heading_style)
        
        activity_data = [['Activity Type', 'CO2e (kg)', 'Count']]
        for act_type, value in sorted(self.summary['activity_breakdown'].items(), 
                                     key=lambda x: x[1], reverse=True):
            count = len([a for a in self.activities if a['type'] == act_type])
            activity_data.append([
                act_type.replace('_', ' ').title(),
                f"{value:,.2f}",
                str(count)
            ])
        
        activity_table = Table(activity_data, colWidths=[3*inch, 2*inch, 2*inch], repeatRows=1)
        activity_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7FA87F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))
        
        elements.append(KeepTogether([type_heading, activity_table]))
        elements.append(PageBreak())
        
        # Detailed Activities Table
        detail_heading = Paragraph("Detailed Activity List", heading_style)
        
        detailed_data = [['#', 'Type', 'Scope', 'Quantity', 'Unit', 'CO2e (kg)', 'Calc Method', 'EF (kgCO2e/unit)', 'Region', 'Date']]
        for i, activity in enumerate(self.activities, 1):
            # Extract quantity and unit from input_data
            input_data = activity.get('input_data', {})
            quantity = None
            unit = 'N/A'
            
            # Try different possible field names in input_data
            if isinstance(input_data, dict):
                # Check for common quantity fields
                for qty_field in ['energy', 'volume', 'weight', 'distance', 'money', 'amount']:
                    if qty_field in input_data:
                        try:
                            quantity = float(input_data[qty_field])
                        except (TypeError, ValueError):
                            pass
                        if quantity is not None:
                            break
                
                # Check for common unit fields
                for unit_field in ['energy_unit', 'volume_unit', 'weight_unit', 'distance_unit', 'money_unit', 'unit']:
                    if unit_field in input_data:
                        unit = input_data[unit_field]
                        break
            
            # Calculate emission factor: EF = CO2e / Quantity
            co2e_value = float(activity.get('co2e_kg', 0) or 0)
            if quantity and quantity > 0:
                emission_factor = f"{co2e_value / quantity:.6f}"
            else:
                emission_factor = 'N/A'
            
            detailed_data.append([
                str(i),
                activity['type'][:15],
                activity['scope'],
                f"{quantity:,.2f}" if quantity is not None else 'N/A',
                unit,
                f"{co2e_value:,.2f}",
                activity.get('calculation_method', 'N/A')[:12],
                emission_factor,
                activity['region'],
                activity['date'][:10] if activity['date'] != 'N/A' else 'N/A'
            ])
        
        detailed_table = Table(detailed_data, 
                      colWidths=[0.3*inch, 1.1*inch, 0.7*inch, 0.7*inch, 0.5*inch, 0.8*inch, 0.8*inch, 1.5*inch, 0.5*inch, 0.8*inch],
                      repeatRows=1)
        detailed_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7FA87F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))
        
        elements.append(KeepTogether([detail_heading, detailed_table]))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def _generate_custom_pdf(self, config: Dict[str, Any], viz_buffer: Optional[io.BytesIO]) -> io.BytesIO:
        """Generate custom PDF based on user configuration"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                              rightMargin=30, leftMargin=30,
                              topMargin=30, bottomMargin=30)
        
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
        
        # Executive Summary (if enabled)
        if config.get('include_executive_summary', True):
            elements.append(Paragraph("Executive Summary", heading_style))
            
            summary_text = f"""
            This report presents a comprehensive analysis of greenhouse gas emissions for 
            {self.project_data['organization']}. During the reporting period, a total of 
            <b>{self.summary['total_activities']}</b> emission activities were recorded, 
            resulting in <b>{self.summary['total_co2e_kg']:,.2f} kg CO2e</b> of total emissions.
            """
            elements.append(Paragraph(summary_text, styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Summary Totals
            summary_heading = Paragraph("Summary Totals", heading_style)
            summary_data = [['Scope', 'CO2e (kg)', '%', 'Activities']]
            
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
            
            summary_data.append([
                'Total',
                f"{self.summary['total_co2e_kg']:,.2f}",
                '100%',
                str(self.summary['total_activities'])
            ])
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch, 1.5*inch, 1.5*inch], repeatRows=1)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7FA87F')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F9F9F9')]),
            ]))
            
            elements.append(KeepTogether([summary_heading, summary_table, Spacer(1, 20)]))
        
        # Visualizations (if enabled and buffer exists)
        if config.get('include_charts', True) and viz_buffer:
            elements.append(Paragraph("Emissions Analysis & Visualizations", heading_style))
            img = Image(viz_buffer, width=7*inch, height=5.25*inch)
            elements.append(img)
            elements.append(PageBreak())
        
        # Custom Tables
        for table_config in config.get('tables', []):
            table_element = self._build_custom_table(table_config, heading_style)
            if table_element:
                elements.extend(table_element)
                if table_config.get('page_break_after', False):
                    elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def _build_custom_table(self, table_config: Dict[str, Any], heading_style) -> List:
        """Build a custom table based on configuration with column filtering"""
        table_type = table_config.get('type')
        title = table_config.get('title')
        selected_columns = table_config.get('columns', [])
        
        # Get full table data
        if table_type == 'activity_data':
            all_columns = ["Activity", "Emission Source", "Activity Data", "Unit", "Scope"]
            full_rows = self._build_activity_summary_rows()
        elif table_type == 'emission_factors':
            all_columns = ["Scope", "Emission Source", "Unit", "kgCO2e per Unit", "Data Source"]
            full_rows = self._build_emission_factor_rows()
        elif table_type == 'gas_breakdown':
            all_columns = ["Scope", "Emission Source", "CO2e (kg)", "CO2 (kg)", "CH4 (kg)", "N2O (kg)", "Other GHGs (kg)"]
            full_rows = self._build_gas_summary_rows()
        elif table_type == 'activity_type_breakdown':
            all_columns = ["Activity Type", "CO2e (kg)", "Count"]
            full_rows = self._build_activity_type_breakdown_rows()
        elif table_type == 'detailed_list':
            all_columns = ["#", "Type", "Scope", "Quantity", "Unit", "CO2e (kg)", "Calc Method", "EF (kgCO2e/unit)", "Region", "Date"]
            full_rows = self._build_detailed_activity_rows()
        elif table_type == 'custom':
            # For custom tables, build a combined table with the requested columns
            all_columns, full_rows = self._build_custom_combined_table(selected_columns)
        else:
            return []
        
        # Filter columns based on selection
        if not selected_columns or len(selected_columns) == 0:
            selected_columns = all_columns  # Use all if none specified
        
        # Find column indices
        header_row = full_rows[0]
        col_indices = []
        filtered_header = []
        
        for col in selected_columns:
            if col in header_row:
                idx = header_row.index(col)
                col_indices.append(idx)
                filtered_header.append(col)
        
        # Filter all rows
        filtered_rows = [filtered_header]
        for row in full_rows[1:]:
            filtered_row = [row[i] for i in col_indices if i < len(row)]
            filtered_rows.append(filtered_row)
        
        # Use custom title if provided, otherwise use default
        if not title:
            title = self._get_default_table_title(table_type)
        
        heading = Paragraph(title, heading_style)
        
        # Calculate column widths dynamically with minimum width constraints
        num_cols = len(filtered_header)
        available_width = 7.3 * inch
        min_col_width = 0.4 * inch  # Minimum width to prevent text overflow
        col_width = max(available_width / num_cols, min_col_width) if num_cols > 0 else 1*inch
        col_widths = [col_width] * num_cols
        
        # Wrap cell content using Paragraph to enable word-wrapping
        styles = getSampleStyleSheet()
        cell_style = ParagraphStyle(
            'Cell',
            parent=styles['Normal'],
            fontSize=7,
            leading=9,
            alignment=TA_LEFT,
        )
        header_cell_style = ParagraphStyle(
            'HeaderCell',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            alignment=TA_LEFT,
        )

        wrapped_rows = []
        for r_idx, row in enumerate(filtered_rows):
            wrapped_row = []
            for cell in row:
                text = str(cell) if cell is not None else ''
                wrapped_row.append(Paragraph(text, header_cell_style if r_idx == 0 else cell_style))
            wrapped_rows.append(wrapped_row)
        
        # Create table with better spacing
        table = Table(wrapped_rows, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7FA87F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
        ]))
        
        return [KeepTogether([heading, table, Spacer(1, 16)])]
    
    def _get_default_table_title(self, table_type: str) -> str:
        """Get default title for table type"""
        titles = {
            'activity_data': 'Activity Data by Scope',
            'emission_factors': 'Emission Factors Used',
            'gas_breakdown': 'GHG Emissions by Scope and Gas',
            'activity_type_breakdown': 'Activity Type Breakdown',
            'detailed_list': 'Detailed Activity List'
        }
        return titles.get(table_type, 'Data Table')
    
    def _build_activity_type_breakdown_rows(self) -> List[List[str]]:
        """Build activity type breakdown table data"""
        rows = [['Activity Type', 'CO2e (kg)', 'Count']]
        for act_type, value in sorted(self.summary['activity_breakdown'].items(), 
                                     key=lambda x: x[1], reverse=True):
            count = len([a for a in self.activities if a['type'] == act_type])
            rows.append([
                act_type.replace('_', ' ').title(),
                f"{value:,.2f}",
                str(count)
            ])
        return rows
    
    def _build_detailed_activity_rows(self) -> List[List[str]]:
        """Build detailed activity list table data"""
        rows = [['#', 'Type', 'Scope', 'Quantity', 'Unit', 'CO2e (kg)', 'Calc Method', 'EF (kgCO2e/unit)', 'Region', 'Date']]
        
        for i, activity in enumerate(self.activities, 1):
            input_data = activity.get('input_data', {})
            quantity = None
            unit = 'N/A'
            
            if isinstance(input_data, dict):
                for qty_field in ['energy', 'volume', 'weight', 'distance', 'money', 'amount']:
                    if qty_field in input_data:
                        try:
                            quantity = float(input_data[qty_field])
                        except (TypeError, ValueError):
                            pass
                        if quantity is not None:
                            break
                
                for unit_field in ['energy_unit', 'volume_unit', 'weight_unit', 'distance_unit', 'money_unit', 'unit']:
                    if unit_field in input_data:
                        unit = input_data[unit_field]
                        break
            
            co2e_value = float(activity.get('co2e_kg', 0) or 0)
            if quantity and quantity > 0:
                emission_factor = f"{co2e_value / quantity:.6f}"
            else:
                emission_factor = 'N/A'
            
            rows.append([
                str(i),
                activity['type'][:15],
                activity['scope'],
                f"{quantity:,.2f}" if quantity is not None else 'N/A',
                unit,
                f"{co2e_value:,.2f}",
                activity.get('calculation_method', 'N/A')[:12],
                emission_factor,
                activity['region'],
                activity['date'][:10] if activity['date'] != 'N/A' else 'N/A'
            ])
        
        return rows
    
    def _build_custom_combined_table(self, selected_columns: List[str]) -> tuple[List[str], List[List[str]]]:
        """Build a combined table that can include any available column per activity"""
        # Canonical set of all supported columns (match frontend labels)
        all_columns = [
            "#", "Activity Data", "Activity Type", "Scope", "Quantity", "Unit",
            "CO2e (kg)", "Calc Method", "EF (kgCO2e/unit)", "kgCO2e per Unit", "Region", "Date",
            "Emission Source", "Data Source", "Count", "CO2 (kg)", "CH4 (kg)", "N2O (kg)", "Other GHGs (kg)"
        ]

        # Helper to generate a per-activity mapping of column -> value
        def build_activity_map(index: int, activity: Dict[str, Any]) -> Dict[str, str]:
            co2e_value = float(activity.get('co2e_kg', 0) or 0)
            quantity, unit = self._extract_quantity_unit(activity)
            source_name, data_source = self._extract_emission_source(activity)

            # Emission factor
            ef_value = None
            if quantity and quantity > 0:
                try:
                    ef_value = co2e_value / float(quantity)
                except Exception:
                    ef_value = None

            # Constituent gases per activity
            co2 = ch4 = n2o = other = None
            input_data = activity.get('input_data', {}) if isinstance(activity.get('input_data', {}), dict) else {}
            autopilot = input_data.get('autopilot_response', {}) if isinstance(input_data.get('autopilot_response', {}), dict) else {}
            gas_breakdown = activity.get('constituent_gases')
            if not gas_breakdown and autopilot:
                gas_breakdown = autopilot.get('constituent_gases') or autopilot.get('constituentGases')
                estimate = autopilot.get('estimate', {}) if isinstance(autopilot.get('estimate', {}), dict) else {}
                if not gas_breakdown and estimate:
                    gas_breakdown = estimate.get('constituent_gases') or estimate.get('constituentGases')
            if isinstance(gas_breakdown, dict) and gas_breakdown:
                try:
                    co2 = float(gas_breakdown.get('co2', 0) or 0)
                except Exception:
                    co2 = None
                try:
                    ch4 = float(gas_breakdown.get('ch4', 0) or 0)
                except Exception:
                    ch4 = None
                try:
                    n2o = float(gas_breakdown.get('n2o', 0) or 0)
                except Exception:
                    n2o = None
                other_total = 0.0
                for gas_key, gas_val in gas_breakdown.items():
                    if str(gas_key).lower() not in ['co2', 'co2e', 'ch4', 'n2o']:
                        try:
                            other_total += float(gas_val)
                        except Exception:
                            pass
                other = other_total if other_total > 0 else None

            # Map values
            act_type_raw = activity.get('type') or 'Unknown'
            act_type_display = str(act_type_raw).replace('_', ' ').title()
            date_display = activity['date'][:10] if activity.get('date') and activity['date'] != 'N/A' else 'N/A'
            quantity_display = f"{quantity:,.2f}" if quantity is not None else 'N/A'
            ef_display = f"{ef_value:.6f}" if ef_value is not None else 'N/A'

            return {
                '#': str(index),
                'Activity Data': quantity_display,
                'Activity Type': act_type_display,
                'Scope': activity.get('scope', 'Unknown'),
                'Quantity': quantity_display,
                'Unit': unit or 'N/A',
                'CO2e (kg)': f"{co2e_value:,.2f}",
                'Calc Method': (activity.get('calculation_method', 'N/A') or 'N/A')[:12],
                'EF (kgCO2e/unit)': ef_display,
                'kgCO2e per Unit': ef_display,
                'Region': activity.get('region', 'N/A') or 'N/A',
                'Date': date_display,
                'Emission Source': source_name or 'Unknown',
                'Data Source': data_source or 'Climatiq API',
                'Count': '1',
                'CO2 (kg)': f"{co2:,.3f}" if co2 is not None else 'N/A',
                'CH4 (kg)': f"{ch4:,.3f}" if ch4 is not None else 'N/A',
                'N2O (kg)': f"{n2o:,.3f}" if n2o is not None else 'N/A',
                'Other GHGs (kg)': f"{other:,.3f}" if other is not None else 'N/A',
            }

        # Build full rows including header (all columns), filtering happens later
        full_rows: List[List[str]] = [all_columns]
        for i, activity in enumerate(self.activities, 1):
            amap = build_activity_map(i, activity)
            full_rows.append([amap.get(col, 'N/A') for col in all_columns])

        return all_columns, full_rows
