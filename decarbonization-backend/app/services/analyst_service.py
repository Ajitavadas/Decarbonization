"""
Analyst Service - The Computer Agent (Phase 2.4)
Responsible for validation, calculation execution, and commitment.
"""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.calculation_service import CalculationService
from app.models.models import EmissionTransaction, FlaggedEvent
from app.schemas.emissions import StandardizedEmissionEvent, LocationData, DataQuality, EmissionResult

logger = logging.getLogger(__name__)

class AnalystService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validates if the input data is sufficient and valid for calculation.
        Checks for:
        - Required fields present
        - Positive values
        - Valid units (supported by CalculationService)
        """
        try:
            # 1. Basic required fields check
            required_fields = ["activity_value", "activity_unit", "activity_type"]
            for field in required_fields:
                if field not in data or data[field] is None:
                    logger.warning(f"Validation failed: Missing field {field}")
                    return False

            # 2. Value validation
            try:
                val = float(data["activity_value"])
                if val < 0:
                     logger.warning(f"Validation failed: Negative activity value {val}")
                     return False
            except ValueError:
                 logger.warning(f"Validation failed: Non-numeric activity value {data.get('activity_value')}")
                 return False

            # 3. Unit validation
            # Check if unit is in CalculationService supported units
            unit = data["activity_unit"].lower().strip()
            if unit not in CalculationService.UNIT_CONVERSIONS:
                logger.warning(f"Validation failed: Unsupported unit {unit}")
                return False

            return True

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    async def execute_calculation(self, event_id: str, verified_data: Dict[str, Any], user_id: str) -> Optional[EmissionTransaction]:
        """
        Executes the calculation pipeline:
        1. Calls CalculationService
        2. Creates EmissionTransaction
        3. Resolves FlaggedEvent (if linked)
        """
        try:
            # 0. Reuse or generate IDs
            # If event_id corresponds to a FlaggedEvent, we will use its organization_id, etc.
            # But the data might come from the user's input "verified_data"
            
            # Fetch flagged event to context if exists
            flagged_event = None
            if event_id:
                result = await self.db.execute(select(FlaggedEvent).where(FlaggedEvent.id == event_id))
                flagged_event = result.scalars().first()

            org_id = verified_data.get("organization_id")
            if not org_id and flagged_event:
                org_id = flagged_event.organization_id
            
            if not org_id:
                raise ValueError("Organization ID is required for calculation")

            # 1. Construct StandardizedEmissionEvent for CalculationService
            # We need to map the flat verified_data to the nested structure
            std_event = StandardizedEmissionEvent(
                event_id=event_id or str(UUID(int=0)), # arbitrary if new
                org_id=org_id,
                timestamp=datetime.now(timezone.utc), # Using current time for the calc event if not provided
                activity_type=verified_data.get("activity_type", "electricity"), # default or need logic
                activity_value=float(verified_data["activity_value"]),
                activity_unit=verified_data["activity_unit"],
                location=LocationData(), # Empty for now if not in data
                data_quality=DataQuality(
                    source_type="user_entry",
                    confidence_score=1.0
                )
            )

            # 2. Calculate
            result: EmissionResult = await CalculationService.calculate_emissions(std_event)

            # 3. Create EmissionTransaction
            transaction = EmissionTransaction(
                organization_id=org_id,
                description=verified_data.get("description", "Analyst Corrected Entry"),
                transaction_date=std_event.timestamp,
                scope=2, # TODO: infer from activity_type, hardcoded for MVP flow as per instructions usually imply scope 2 or 1
                category=std_event.activity_type,
                activity_value=std_event.activity_value,
                activity_unit=std_event.activity_unit,
                emission_factor_value=result.factor_used.get("value", 0.0),
                co2e_kg=result.location_based_co2e_kg,
                co2e_tonnes=result.location_based_co2e_kg / 1000.0,
                created_by_user_id=user_id,
                verified_by_user_id=user_id,
                verified_at=datetime.now(timezone.utc),
                notes=f"Resolved from event {event_id}" if flagged_event else "Manual entry via Analyst"
            )
            
            self.db.add(transaction)

            # 4. Resolve FlaggedEvent if it exists
            if flagged_event:
                flagged_event.status = "resolved"
                flagged_event.resolved_at = datetime.now(timezone.utc)
                flagged_event.resolved_by_user_id = user_id
                flagged_event.resolution_notes = f"Resolved by Analyst Agent with value {std_event.activity_value} {std_event.activity_unit}"
                # self.db.add(flagged_event) # already attached to session

            await self.db.commit()
            await self.db.refresh(transaction)
            
            logger.info(f"Analyst execution successful. Transaction {transaction.id} created.")
            return transaction

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Analyst execution failed: {e}")
            raise
