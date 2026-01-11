"""
Anomaly Detector Service
Detects statistical outliers and implausible values in emission data
"""

import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from collections import defaultdict
from uuid import UUID
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.activity import EmissionActivity
from app.models.project import Project
from app.core.archetype_config import get_archetype, ArchetypeFingerprint

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in emission activity data
    
    Detection Types:
    - Statistical Outliers: Z-score > 3 on monthly totals
    - Zero Values: co2e_kg = 0 with non-zero inputs
    - Implausible Values: Domain-specific thresholds
    - Scope Distribution: Misalignment with archetype expectations
    """
    
    # Thresholds for implausible values (kg CO2e per unit)
    IMPLAUSIBLE_THRESHOLDS = {
        "electricity": {"min": 0.001, "max": 100},  # per kWh
        "fuel": {"min": 0.1, "max": 50},  # per liter
        "business_travel": {"min": 0.01, "max": 10},  # per km
        "procurement": {"min": 0.0001, "max": 100},  # per currency unit
    }
    
    def __init__(self, db: Session, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id
    
    def detect_all_anomalies(
        self,
        project_id: Optional[UUID] = None,
        archetype: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Run all anomaly detection rules
        
        Args:
            project_id: Optional specific project to audit
            archetype: Organization's emission archetype
            
        Returns:
            List of anomaly findings
        """
        findings = []
        
        # Get activities scoped to organization
        query = self.db.query(EmissionActivity).join(Project).filter(
            Project.organization_id == self.organization_id
        )
        
        if project_id:
            query = query.filter(Project.id == project_id)
        
        activities = query.all()
        
        if not activities:
            return findings  # No data to analyze
        
        # Run detection rules
        findings.extend(self._detect_zero_values(activities))
        findings.extend(self._detect_statistical_outliers(activities))
        findings.extend(self._detect_implausible_values(activities))
        findings.extend(self._detect_scope_distribution_anomaly(activities, archetype))
        findings.extend(self._detect_seasonal_anomalies(activities))
        
        # Filter out suppressed findings
        findings = self._filter_suppressed(findings)
        
        return findings
    
    def _detect_seasonal_anomalies(
        self,
        activities: List[EmissionActivity]
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies based on seasonal baselines.
        
        Flags activities that are significantly above or below the
        expected P90/P10 for their activity type and month.
        """
        from app.models.activity_baseline import ActivityBaseline
        
        findings = []
        month_names = ["", "January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        
        for activity in activities:
            if not activity.co2e_kg or not activity.activity_date:
                continue
            
            month = activity.activity_date.month
            
            # Get baseline for this activity type and month
            baseline = self.db.query(ActivityBaseline).filter(
                ActivityBaseline.organization_id == self.organization_id,
                ActivityBaseline.activity_type == activity.activity_type,
                ActivityBaseline.month == month
            ).first()
            
            if not baseline or baseline.sample_count < 3:
                continue  # Not enough history
            
            value = float(activity.co2e_kg)
            p90 = float(baseline.p90) if baseline.p90 else 0
            p10 = float(baseline.p10) if baseline.p10 else 0
            
            # Check for unusually high values (>1.5x P90)
            if p90 > 0 and value > p90 * 1.5:
                input_data = activity.input_data or {}
                findings.append({
                    "flag_type": "seasonal_anomaly",
                    "severity": "warning",
                    "rule_id": "seasonal_above_p90",
                    "title": f"{activity.activity_type.title()} unusually high for {month_names[month]}",
                    "description": f"Activity has {value:,.0f} kg CO₂e, which is significantly above the typical range ({p10:,.0f} - {p90:,.0f} kg) for {month_names[month]}.",
                    "recommendation": "Verify this activity data is correct. It may indicate a data entry error or unusual operational event.",
                    "evidence": {
                        "activity_id": str(activity.id),
                        "activity_type": activity.activity_type,
                        "month": month,
                        "month_name": month_names[month],
                        "value": round(value, 2),
                        "expected_range": f"{p10:,.0f} - {p90:,.0f}",
                        "baseline_samples": baseline.sample_count,
                        "description": input_data.get("description", "")[:100]
                    },
                    "activity_id": activity.id
                })
            
            # Check for unusually low values (<0.5x P10)
            elif p10 > 0 and value < p10 * 0.5 and value > 0:
                input_data = activity.input_data or {}
                findings.append({
                    "flag_type": "seasonal_anomaly",
                    "severity": "info",
                    "rule_id": "seasonal_below_p10",
                    "title": f"{activity.activity_type.title()} unusually low for {month_names[month]}",
                    "description": f"Activity has {value:,.0f} kg CO₂e, which is significantly below the typical range ({p10:,.0f} - {p90:,.0f} kg) for {month_names[month]}.",
                    "recommendation": "This could be positive progress in emissions reduction, or it may indicate missing data. Please verify.",
                    "evidence": {
                        "activity_id": str(activity.id),
                        "activity_type": activity.activity_type,
                        "month": month,
                        "month_name": month_names[month],
                        "value": round(value, 2),
                        "expected_range": f"{p10:,.0f} - {p90:,.0f}",
                        "baseline_samples": baseline.sample_count,
                        "description": input_data.get("description", "")[:100]
                    },
                    "activity_id": activity.id
                })
        
        return findings
    
    def _filter_suppressed(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out findings that match active suppression rules."""
        from app.models.suppression_rule import SuppressionRule
        from datetime import datetime
        
        # Get active suppression rules
        rules = self.db.query(SuppressionRule).filter(
            SuppressionRule.organization_id == self.organization_id,
            SuppressionRule.is_active == True,
            SuppressionRule.expires_at > datetime.utcnow()
        ).all()
        
        if not rules:
            return findings
        
        filtered = []
        for finding in findings:
            is_suppressed = False
            for rule in rules:
                if rule.matches(finding):
                    logger.debug(f"Suppressing finding {finding.get('rule_id')} due to rule {rule.id}")
                    is_suppressed = True
                    break
            
            if not is_suppressed:
                filtered.append(finding)
        
        return filtered
    
    def _detect_zero_values(
        self,
        activities: List[EmissionActivity]
    ) -> List[Dict[str, Any]]:
        """
        Detect activities with zero CO2e but non-zero inputs
        """
        findings = []
        
        for activity in activities:
            if activity.co2e_kg == 0 or activity.co2e_kg == Decimal("0"):
                # Check if input data has non-zero values
                input_data = activity.input_data or {}
                amount = input_data.get("amount", 0)
                
                if amount and float(amount) > 0:
                    findings.append({
                        "flag_type": "anomaly",
                        "severity": "warning",
                        "rule_id": "zero_co2e_nonzero_input",
                        "title": f"Zero emissions for {activity.activity_type} activity",
                        "description": f"Activity has {amount} {input_data.get('unit', 'units')} input but calculated 0 kg CO2e. This may indicate a calculation error.",
                        "recommendation": "Review the emission factor selection and calculation parameters for this activity.",
                        "evidence": {
                            "activity_id": str(activity.id),
                            "activity_type": activity.activity_type,
                            "input_amount": float(amount),
                            "input_unit": input_data.get("unit"),
                            "co2e_kg": float(activity.co2e_kg),
                            "description": input_data.get("description", "")[:100]
                        },
                        "activity_id": activity.id
                    })
        
        return findings
    
    def _detect_statistical_outliers(
        self,
        activities: List[EmissionActivity]
    ) -> List[Dict[str, Any]]:
        """
        Detect statistical outliers using Z-score method
        Flags activities with Z-score > 3
        """
        findings = []
        
        # Group by activity type for meaningful comparison
        by_type: Dict[str, List[EmissionActivity]] = defaultdict(list)
        for activity in activities:
            if activity.co2e_kg and float(activity.co2e_kg) > 0:
                by_type[activity.activity_type].append(activity)
        
        for activity_type, type_activities in by_type.items():
            if len(type_activities) < 5:
                continue  # Need enough data for statistics
            
            values = [float(a.co2e_kg) for a in type_activities]
            
            try:
                mean = statistics.mean(values)
                stdev = statistics.stdev(values)
                
                if stdev == 0:
                    continue
                
                for activity in type_activities:
                    value = float(activity.co2e_kg)
                    z_score = abs((value - mean) / stdev)
                    
                    if z_score > 3:
                        input_data = activity.input_data or {}
                        findings.append({
                            "flag_type": "anomaly",
                            "severity": "warning" if z_score < 4 else "critical",
                            "rule_id": "statistical_outlier_zscore",
                            "title": f"Statistical outlier in {activity_type}",
                            "description": f"Activity has {value:.2f} kg CO2e which is {z_score:.1f} standard deviations from the mean ({mean:.2f} kg). This is unusually high/low compared to similar activities.",
                            "recommendation": "Verify the input data and calculation for this activity. It may be an error or require investigation.",
                            "evidence": {
                                "activity_id": str(activity.id),
                                "activity_type": activity_type,
                                "co2e_kg": value,
                                "z_score": round(z_score, 2),
                                "mean": round(mean, 2),
                                "stdev": round(stdev, 2),
                                "description": input_data.get("description", "")[:100]
                            },
                            "activity_id": activity.id
                        })
            except statistics.StatisticsError:
                continue
        
        return findings
    
    def _detect_implausible_values(
        self,
        activities: List[EmissionActivity]
    ) -> List[Dict[str, Any]]:
        """
        Detect values outside domain-specific thresholds
        """
        findings = []
        
        for activity in activities:
            if not activity.co2e_kg or activity.activity_type not in self.IMPLAUSIBLE_THRESHOLDS:
                continue
            
            input_data = activity.input_data or {}
            amount = input_data.get("amount", 0)
            
            if not amount or float(amount) <= 0:
                continue
            
            # Calculate emission intensity (kg CO2e per unit)
            intensity = float(activity.co2e_kg) / float(amount)
            
            thresholds = self.IMPLAUSIBLE_THRESHOLDS[activity.activity_type]
            
            if intensity < thresholds["min"] or intensity > thresholds["max"]:
                is_too_low = intensity < thresholds["min"]
                
                findings.append({
                    "flag_type": "anomaly",
                    "severity": "warning",
                    "rule_id": "implausible_emission_intensity",
                    "title": f"Implausible emission intensity for {activity.activity_type}",
                    "description": f"Calculated emission intensity of {intensity:.4f} kg CO2e/{input_data.get('unit', 'unit')} is {'below' if is_too_low else 'above'} the expected range ({thresholds['min']}-{thresholds['max']}).",
                    "recommendation": "Review the emission factor and unit normalization for this activity.",
                    "evidence": {
                        "activity_id": str(activity.id),
                        "activity_type": activity.activity_type,
                        "co2e_kg": float(activity.co2e_kg),
                        "input_amount": float(amount),
                        "input_unit": input_data.get("unit"),
                        "intensity": round(intensity, 6),
                        "expected_range": thresholds,
                        "description": input_data.get("description", "")[:100]
                    },
                    "activity_id": activity.id
                })
        
        return findings
    
    def _detect_scope_distribution_anomaly(
        self,
        activities: List[EmissionActivity],
        archetype: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Detect when scope distribution doesn't match archetype expectations
        """
        findings = []
        
        if not archetype:
            return findings
        
        fingerprint = get_archetype(archetype)
        if not fingerprint:
            return findings
        
        # Calculate actual scope distribution
        scope_totals: Dict[str, float] = defaultdict(float)
        total_co2e = 0.0
        
        for activity in activities:
            if activity.co2e_kg and activity.scope:
                value = float(activity.co2e_kg)
                scope_totals[activity.scope] += value
                total_co2e += value
        
        if total_co2e == 0:
            return findings
        
        # Calculate ratios
        actual_distribution = {
            scope: value / total_co2e 
            for scope, value in scope_totals.items()
        }
        
        expected = fingerprint.scope_distribution
        thresholds = fingerprint.thresholds
        
        # Check threshold violations
        for threshold_name, threshold_value in thresholds.items():
            if threshold_name.startswith("max_scope1"):
                actual = actual_distribution.get("Scope 1", 0)
                if actual > threshold_value:
                    findings.append({
                        "flag_type": "archetype_mismatch",
                        "severity": "warning",
                        "rule_id": "scope_distribution_scope1_high",
                        "title": f"Scope 1 emissions higher than expected for {fingerprint.display_name}",
                        "description": f"Scope 1 represents {actual*100:.1f}% of total emissions, but for '{fingerprint.display_name}' organizations, it typically should be below {threshold_value*100:.1f}%.",
                        "recommendation": "Review if all Scope 1 activities are correctly classified, or if your organization has unusual direct emission sources.",
                        "evidence": {
                            "archetype": archetype,
                            "actual_scope1_ratio": round(actual, 3),
                            "expected_max_ratio": threshold_value,
                            "actual_distribution": {k: round(v, 3) for k, v in actual_distribution.items()},
                            "expected_distribution": expected
                        }
                    })
            
            elif threshold_name.startswith("min_scope3"):
                actual = actual_distribution.get("Scope 3", 0)
                if actual < threshold_value:
                    findings.append({
                        "flag_type": "archetype_mismatch",
                        "severity": "warning",
                        "rule_id": "scope_distribution_scope3_low",
                        "title": f"Scope 3 emissions lower than expected for {fingerprint.display_name}",
                        "description": f"Scope 3 represents {actual*100:.1f}% of total emissions, but for '{fingerprint.display_name}' organizations, it typically should be above {threshold_value*100:.1f}%.",
                        "recommendation": "Consider whether supply chain, business travel, or other Scope 3 categories are being underreported.",
                        "evidence": {
                            "archetype": archetype,
                            "actual_scope3_ratio": round(actual, 3),
                            "expected_min_ratio": threshold_value,
                            "actual_distribution": {k: round(v, 3) for k, v in actual_distribution.items()},
                            "expected_distribution": expected
                        }
                    })
            
            elif threshold_name.startswith("min_scope1"):
                actual = actual_distribution.get("Scope 1", 0)
                if actual < threshold_value:
                    findings.append({
                        "flag_type": "archetype_mismatch",
                        "severity": "warning",
                        "rule_id": "scope_distribution_scope1_low",
                        "title": f"Scope 1 emissions lower than expected for {fingerprint.display_name}",
                        "description": f"Scope 1 represents {actual*100:.1f}% of total emissions, but for '{fingerprint.display_name}' organizations, it typically should be above {threshold_value*100:.1f}%.",
                        "recommendation": "Review if all direct combustion, fleet vehicles, and process emissions are being captured.",
                        "evidence": {
                            "archetype": archetype,
                            "actual_scope1_ratio": round(actual, 3),
                            "expected_min_ratio": threshold_value,
                            "actual_distribution": {k: round(v, 3) for k, v in actual_distribution.items()},
                            "expected_distribution": expected
                        }
                    })
        
        return findings


# Factory function
def create_anomaly_detector(db: Session, organization_id: UUID) -> AnomalyDetector:
    """Create an anomaly detector instance scoped to an organization"""
    return AnomalyDetector(db, organization_id)
