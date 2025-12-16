"""
Gap Detection Service - Phase 2.1
Logic to detect "Missing Data Gaps" based on heuristic rules.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, distinct

from app.models.models import EmissionTransaction, EmissionFactor

logger = logging.getLogger(__name__)

@dataclass
class GapEvent:
    type: str  # "heating_consistency", "sequence_gap"
    description: str
    severity: str  # "low", "medium", "high"
    details: Dict
    confidence_score: float

class GapService:
    
    # Configuration for "Cold" regions and "Winter" months
    # In a real system, this might be more dynamic or database-backed
    COLD_REGIONS = ["US-NE", "US-NY", "US-MW", "EU-NORTH", "CA"]
    WINTER_MONTHS = [12, 1, 2]  # Dec, Jan, Feb
    HEATING_CATEGORIES = ["Natural Gas", "Heating Oil", "Stationary Combustion"]

    @staticmethod
    async def detect_gaps(
        db: AsyncSession,
        org_id: str
    ) -> List[GapEvent]:
        """
        Detect gaps for an organization using all heuristic rules.
        """
        gaps = []
        
        # Fetch transactions for the last year for analysis
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        query = select(EmissionTransaction).where(
            and_(
                EmissionTransaction.organization_id == org_id,
                EmissionTransaction.transaction_date >= one_year_ago
            )
        )
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        # Run Rule 1: Heating Consistency
        gaps.extend(await GapService._check_heating_consistency(db, org_id, transactions))
        
        # Run Rule 2: Sequence Gaps
        gaps.extend(GapService._check_sequence_gaps(transactions))
        
        return gaps

    @staticmethod
    async def _check_heating_consistency(
        db: AsyncSession,
        org_id: str,
        transactions: List[EmissionTransaction]
    ) -> List[GapEvent]:
        """
        Rule 1: "Heating Consistency"
        If Grid Region is 'Cold' and Month is 'Winter', expect 'Natural Gas' or 'Heating Oil' scope 1 transactions.
        
        We infer 'Grid Region' from the emission factors used by the organization.
        """
        gaps = []
        
        # 1. Infer Regions
        # Find distinct regions from emission factors used by this org's transactions
        # This is a simplification; ideally we'd have explicit Location data linked to regions.
        factor_ids = {tx.emission_factor_id for tx in transactions if tx.emission_factor_id}
        
        if not factor_ids:
            return []

        # In a real scenario, we might query EmissionFactors related to these IDs
        # Here we will do a join query to find regions
        query = select(distinct(EmissionFactor.region)).where(
            EmissionFactor.id.in_(factor_ids)
        )
        result = await db.execute(query)
        detected_regions = [r for r in result.scalars().all() if r]
        
        is_cold_region = any(region in GapService.COLD_REGIONS for region in detected_regions)
        
        if not is_cold_region:
            return []

        # 2. Check for Winter Heating Data
        has_heating_data = False
        winter_months_present = set()
        
        for tx in transactions:
            if tx.transaction_date.month in GapService.WINTER_MONTHS:
                if tx.scope == 1 and any(cat.lower() in tx.category.lower() for cat in GapService.HEATING_CATEGORIES):
                    has_heating_data = True
                    winter_months_present.add(tx.transaction_date.month)
        
        # If in a cold region, check for missing winter heating data
        if not has_heating_data:
             gaps.append(GapEvent(
                type="heating_consistency",
                description="Missing heating data (Natural Gas/Oil) in cold region during winter months.",
                severity="high",
                details={
                    "detected_regions": detected_regions,
                    "missing_months": ["Dec", "Jan", "Feb"]
                },
                confidence_score=0.85
            ))
        else:
             # Check for partial missing months (e.g. have Jan but missing Feb)
             missing_winter_months = []
             for month in GapService.WINTER_MONTHS:
                 if month not in winter_months_present:
                     # Check if we are past this month in the current year context? 
                     # For simplicity, we just check if it's missing from the loaded dataset window
                     # Only flag if the month has passed. 
                     # (e.g. don't flag missing Dec 2024 if it's only Nov 2024)
                     # Since we loaded "last 365 days", these months should be present if they occurred.
                     missing_winter_months.append(month)
            
             if missing_winter_months:
                 month_names = [datetime(2000, m, 1).strftime('%b') for m in missing_winter_months]
                 gaps.append(GapEvent(
                    type="heating_consistency",
                    description=f"Partial missing heating data in cold region. Missing months: {', '.join(month_names)}",
                    severity="medium",
                    details={
                        "detected_regions": detected_regions,
                        "missing_months": month_names
                    },
                    confidence_score=0.75
                 ))

        return gaps

    @staticmethod
    def _check_sequence_gaps(
        transactions: List[EmissionTransaction]
    ) -> List[GapEvent]:
        """
        Rule 2: "Sequence Gaps"
        If data exists for Month X and Month X+2, flag missing Month X+1 within the same category.
        """
        gaps = []
        
        # Group by category
        by_category = {}
        for tx in transactions:
            if tx.category not in by_category:
                by_category[tx.category] = []
            by_category[tx.category].append(tx)
            
        for category, txs in by_category.items():
            # Get all unique year-months present
            # Format: 'YYYY-MM'
            present_months = sorted(list(set(tx.transaction_date.strftime("%Y-%m") for tx in txs)))
            
            if len(present_months) < 2:
                continue
                
            # Iterate through months and check for gaps
            # We convert YYYY-MM to a comparable integer or date object
            dates = [datetime.strptime(m, "%Y-%m") for m in present_months]
            
            for i in range(len(dates) - 1):
                current = dates[i]
                next_date = dates[i+1]
                
                # Check variance in months
                # Calculate month difference: (y2-y1)*12 + (m2-m1)
                month_diff = (next_date.year - current.year) * 12 + (next_date.month - current.month)
                
                if month_diff > 1:
                    # There is a gap
                    missing_count = month_diff - 1
                    
                    # Generate list of missing months for description
                    curr_iter = current
                    missing_list = []
                    for _ in range(missing_count):
                        curr_iter = curr_iter.replace(day=1) + timedelta(days=32)
                        curr_iter = curr_iter.replace(day=1) # Normalize to 1st of month
                        missing_list.append(curr_iter.strftime("%Y-%m"))
                    
                    gaps.append(GapEvent(
                        type="sequence_gap",
                        description=f"Missing data for {category} between {current.strftime('%Y-%m')} and {next_date.strftime('%Y-%m')}",
                        severity="medium",
                        details={
                            "category": category,
                            "gap_start": current.strftime("%Y-%m"),
                            "gap_end": next_date.strftime("%Y-%m"),
                            "missing_months": missing_list
                        },
                        confidence_score=0.9
                    ))
                    
        return gaps
