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

from app.models.models import EmissionTransaction

logger = logging.getLogger(__name__)


class AnomalyService:
    """
    Anomaly Detection Service (US-4.2)
    
    AC:
    - System detects 90% or more of actual anomalies
    - False positive rate is under 10%
    - Each flagged item includes clear explanation
    - Alert queue updates in real-time
    """
    
    @staticmethod
    async def detect_anomalies(
        db: AsyncSession,
        org_id: str,
        lookback_days: int = 90
    ) -> List[Dict]:
        """
        Detect anomalous transactions using statistical methods
        
        Returns:
            List of anomaly dictionaries with explanations
        """
        anomalies = []
        
        # Get historical transactions
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        
        query = select(EmissionTransaction).where(
            and_(
                EmissionTransaction.organization_id == org_id,
                EmissionTransaction.transaction_date >= cutoff_date
            )
        )
        
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        if len(transactions) < 10:
            logger.info("Not enough data for anomaly detection")
            return []
        
        # Group by category for better detection
        by_category = {}
        for tx in transactions:
            if tx.category not in by_category:
                by_category[tx.category] = []
            by_category[tx.category].append(tx)
        
        # Detect anomalies within each category
        for category, txs in by_category.items():
            if len(txs) < 5:
                continue
            
            values = [tx.co2e_tonnes for tx in txs]
            mean = np.mean(values)
            std = np.std(values)
            
            # Use 3-sigma rule for outliers
            threshold_high = mean + (3 * std)
            threshold_low = max(0, mean - (3 * std))
            
            for tx in txs:
                if tx.co2e_tonnes > threshold_high:
                    anomalies.append({
                        "transaction_id": tx.id,
                        "type": "high_value",
                        "severity": "high" if tx.co2e_tonnes > threshold_high * 1.5 else "medium",
                        "value": tx.co2e_tonnes,
                        "expected_range": f"{threshold_low:.2f} - {threshold_high:.2f}",
                        "deviation": f"{((tx.co2e_tonnes - mean) / std):.2f} std deviations",
                        "explanation": f"Unusually high emission for {category}: {tx.co2e_tonnes:.2f} tonnes (expected: {mean:.2f}±{std:.2f})",
                        "category": category,
                        "detected_at": datetime.now(timezone.utc).isoformat()
                    })
                
                elif tx.co2e_tonnes < threshold_low and tx.co2e_tonnes > 0:
                    anomalies.append({
                        "transaction_id": tx.id,
                        "type": "low_value",
                        "severity": "low",
                        "value": tx.co2e_tonnes,
                        "expected_range": f"{threshold_low:.2f} - {threshold_high:.2f}",
                        "deviation": f"{((mean - tx.co2e_tonnes) / std):.2f} std deviations",
                        "explanation": f"Unusually low emission for {category}: {tx.co2e_tonnes:.2f} tonnes (expected: {mean:.2f}±{std:.2f})",
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
        """Detect missing or incomplete data"""
        anomalies = []
        
        # Check for missing required fields
        query = select(EmissionTransaction).where(
            and_(
                EmissionTransaction.organization_id == org_id,
                EmissionTransaction.transaction_date >= datetime.now(timezone.utc) - timedelta(days=lookback_days)
            )
        )
        
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        for tx in transactions:
            issues = []
            
            if not tx.description or len(tx.description.strip()) < 5:
                issues.append("missing or incomplete description")
            
            if tx.activity_value <= 0:
                issues.append("invalid activity value")
            
            if tx.emission_factor_value <= 0:
                issues.append("invalid emission factor")
            
            if issues:
                anomalies.append({
                    "transaction_id": tx.id,
                    "type": "data_quality",
                    "severity": "medium",
                    "explanation": f"Data quality issues: {', '.join(issues)}",
                    "detected_at": datetime.now(timezone.utc).isoformat()
                })
        
        return anomalies