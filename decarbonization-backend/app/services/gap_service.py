from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, distinct, join
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

from app.models.models import EmissionEvent, CalculationLedger, EmissionFactor

logger = logging.getLogger(__name__)

@dataclass
class GapEvent:
    type: str  # "heating_consistency", "sequence_gap"
    description: str
    severity: str  # "low", "medium", "high"
    details: Dict
    confidence_score: float

class GapService:
    
    COLD_REGIONS = ["US-NE", "US-NY", "US-MW", "EU-NORTH", "CA"]
    WINTER_MONTHS = [12, 1, 2]  # Dec, Jan, Feb
    HEATING_CATEGORIES = ["Natural Gas", "Heating Oil", "Stationary Combustion", "Purchased Gas"]

    @staticmethod
    async def detect_gaps(
        db: AsyncSession,
        org_id: str
    ) -> List[GapEvent]:
        """
        Detect gaps for an organization using all heuristic rules.
        """
        gaps = []
        
        # Fetch events for the last year
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
        query = select(EmissionEvent).where(
            and_(
                EmissionEvent.organization_id == org_id,
                EmissionEvent.activity_date >= one_year_ago
            )
        )
        result = await db.execute(query)
        events = result.scalars().all()
        
        # We also need ledger info for some checks (e.g. factors)
        # But for basic gap detection, events are enough.
        
        # Run Rule 1: Heating Consistency
        gaps.extend(await GapService._check_heating_consistency(db, org_id, events))
        
        # Run Rule 2: Sequence Gaps
        gaps.extend(GapService._check_sequence_gaps(events))
        
        return gaps

    @staticmethod
    async def _check_heating_consistency(
        db: AsyncSession,
        org_id: str,
        events: List[EmissionEvent]
    ) -> List[GapEvent]:
        """
        Rule 1: "Heating Consistency"
        """
        gaps = []
        
        # Infer Regions from events and their linked factors via Ledgers
        # For simplicity, we'll check regions if possible.
        # This part might need joining ledgers. 
        # But if we don't have location data yet, we might skip.
        # Let's assume we check for heating in generic cold months.
        
        winter_months_present = set()
        has_heating_data = False
        
        for event in events:
            if event.activity_date.month in GapService.WINTER_MONTHS:
                # We use scope or category. Since scope might be a string now "Scope 1", etc.
                if event.scope == "Scope 1" and any(cat.lower() in (event.scope_3_category or "").lower() for cat in GapService.HEATING_CATEGORIES):
                    has_heating_data = True
                    winter_months_present.add(event.activity_date.month)
        
        # Simple heuristic: if no heating data at all in winter
        if not has_heating_data:
             gaps.append(GapEvent(
                type="heating_consistency",
                description="Missing heating data (Natural Gas/Oil) in winter months.",
                severity="high",
                details={
                    "missing_months": ["Dec", "Jan", "Feb"]
                },
                confidence_score=0.85
            ))
        else:
             missing_winter_months = []
             for month in GapService.WINTER_MONTHS:
                 if month not in winter_months_present:
                     missing_winter_months.append(month)
            
             if missing_winter_months:
                  month_names = [datetime(2000, m, 1).strftime('%b') for m in missing_winter_months]
                  gaps.append(GapEvent(
                    type="heating_consistency",
                    description=f"Partial missing heating data. Missing months: {', '.join(month_names)}",
                    severity="medium",
                    details={
                        "missing_months": month_names
                    },
                    confidence_score=0.75
                  ))

        return gaps

    @staticmethod
    def _check_sequence_gaps(
        events: List[EmissionEvent]
    ) -> List[GapEvent]:
        """
        Rule 2: "Sequence Gaps"
        """
        gaps = []
        
        # Group by activity_type (category)
        by_type = {}
        for event in events:
            type_key = event.scope_3_category or "Main"
            if type_key not in by_type:
                by_type[type_key] = []
            by_type[type_key].append(event)
            
        for type_key, evs in by_type.items():
            present_months = sorted(list(set(event.activity_date.strftime("%Y-%m") for event in evs)))
            
            if len(present_months) < 2:
                continue
                
            dates = [datetime.strptime(m, "%Y-%m") for m in present_months]
            
            for i in range(len(dates) - 1):
                current = dates[i]
                next_date = dates[i+1]
                month_diff = (next_date.year - current.year) * 12 + (next_date.month - current.month)
                
                if month_diff > 1:
                    missing_count = month_diff - 1
                    curr_iter = current
                    missing_list = []
                    for _ in range(missing_count):
                        curr_iter = curr_iter.replace(day=1) + timedelta(days=32)
                        curr_iter = curr_iter.replace(day=1) 
                        missing_list.append(curr_iter.strftime("%Y-%m"))
                    
                    gaps.append(GapEvent(
                        type="sequence_gap",
                        description=f"Missing data for {type_key} between {current.strftime('%Y-%m')} and {next_date.strftime('%Y-%m')}",
                        severity="medium",
                        details={
                            "category": type_key,
                            "gap_start": current.strftime("%Y-%m"),
                            "gap_end": next_date.strftime("%Y-%m"),
                            "missing_months": missing_list
                        },
                        confidence_score=0.9
                    ))
                    
        return gaps
