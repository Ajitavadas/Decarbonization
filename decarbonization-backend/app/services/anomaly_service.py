"""
Anomaly Detection - US-4.2
Automatic detection of unusual transactions
"""

import logging
from typing import List, Dict, Tuple
from datetime import datetime, timedelta, timezone
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.models import EmissionEvent, CalculationLedger

logger = logging.getLogger(__name__)


class AnomalyService:
    """
    Anomaly Detection Service (US-4.2)
    """
    
    @staticmethod
    async def detect_anomalies(
        db: AsyncSession,
        org_id: str,
        lookback_days: int = 90
    ) -> List[Dict]:
        """
        Detect anomalous transactions using statistical methods
        """
        anomalies = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        
        query = (
            select(
                CalculationLedger.id,
                CalculationLedger.result_kg_co2e,
                EmissionEvent.activity_date,
                EmissionEvent.scope_3_category
            )
            .join(EmissionEvent, CalculationLedger.emission_event_id == EmissionEvent.id)
            .where(
                and_(
                    CalculationLedger.organization_id == org_id,
                    EmissionEvent.activity_date >= cutoff_date
                )
            )
        )
        
        result = await db.execute(query)
        transactions = result.all()
        
        if len(transactions) < 10:
            logger.info("Not enough data for anomaly detection")
            return []
        
        # Group by category
        by_category = {}
        for tx in transactions:
            cat = tx.scope_3_category or "Main"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(tx)
        
        for category, txs in by_category.items():
            if len(txs) < 5:
                continue
            
            # Use tonnes for easier reading
            values = [float(tx.result_kg_co2e) / 1000.0 for tx in txs]
            mean = np.mean(values)
            std = np.std(values)
            
            if std == 0: continue # No deviation possible
            
            threshold_high = mean + (3 * std)
            threshold_low = max(0, mean - (3 * std))
            
            for tx in txs:
                val_tonnes = float(tx.result_kg_co2e) / 1000.0
                if val_tonnes > threshold_high:
                    anomalies.append({
                        "calculation_id": tx.id,
                        "type": "high_value",
                        "severity": "high" if val_tonnes > threshold_high * 1.5 else "medium",
                        "value": round(val_tonnes, 2),
                        "explanation": f"Unusually high emission for {category}: {val_tonnes:.2f} tonnes (expected: {mean:.2f}±{std:.2f})",
                        "category": category,
                        "detected_at": datetime.now(timezone.utc).isoformat()
                    })
                
                elif val_tonnes < threshold_low and val_tonnes > 0:
                    anomalies.append({
                        "calculation_id": tx.id,
                        "type": "low_value",
                        "severity": "low",
                        "value": round(val_tonnes, 2),
                        "explanation": f"Unusually low emission for {category}: {val_tonnes:.2f} tonnes (expected: {mean:.2f}±{std:.2f})",
                        "category": category,
                        "detected_at": datetime.now(timezone.utc).isoformat()
                    })
        
        # Detect missing data anomalies
        missing_anomalies = await AnomalyService._detect_missing_data(db, org_id, lookback_days)
        anomalies.extend(missing_anomalies)
        
        logger.info(f"Detected {len(anomalies)} anomalies")
        return anomalies
    
    @staticmethod
    async def _detect_missing_data(
        db: AsyncSession,
        org_id: str,
        lookback_days: int
    ) -> List[Dict]:
        anomalies = []
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        query = (
            select(
                CalculationLedger.id,
                CalculationLedger.result_kg_co2e,
                CalculationLedger.emission_factor_value
            )
            .where(
                and_(
                    CalculationLedger.organization_id == org_id,
                    CalculationLedger.calculation_timestamp >= cutoff_date
                )
            )
        )
        
        result = await db.execute(query)
        ledgers = result.all()
        
        for ledger in ledgers:
            issues = []
            if float(ledger.result_kg_co2e) <= 0:
                issues.append("zero or negative co2e result")
            
            if float(ledger.emission_factor_value) <= 0:
                issues.append("invalid emission factor value")
            
            if issues:
                anomalies.append({
                    "calculation_id": ledger.id,
                    "type": "data_quality",
                    "severity": "medium",
                    "explanation": f"Data quality issues: {', '.join(issues)}",
                    "detected_at": datetime.now(timezone.utc).isoformat()
                })
        
        return anomalies