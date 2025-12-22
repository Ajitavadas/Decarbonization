"""
Analyst Service - The Computer Agent (Phase 2.4)
Responsible for validation, calculation execution, and commitment.
"""

from typing import Dict, Any, Optional
from uuid import UUID
import uuid
from datetime import datetime, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.calculation_service import CalculationService
from app.models.models import EmissionEvent, CalculationLedger, FlaggedEvent, EmissionFactor
from app.schemas.emissions import StandardizedEmissionEvent, LocationData, DataQuality, EmissionResult

logger = logging.getLogger(__name__)

class AnalystService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """
        Validates if the input data is sufficient and valid for calculation.
        """
        try:
            required_fields = ["activity_value", "activity_unit", "activity_type"]
            for field in required_fields:
                if field not in data or data[field] is None:
                    logger.warning(f"Validation failed: Missing field {field}")
                    return False

            try:
                val = float(data["activity_value"])
                if val < 0:
                     logger.warning(f"Validation failed: Negative activity value {val}")
                     return False
            except ValueError:
                 logger.warning(f"Validation failed: Non-numeric activity value {data.get('activity_value')}")
                 return False

            unit = data["activity_unit"].lower().strip()
            if unit not in CalculationService.UNIT_CONVERSIONS:
                logger.warning(f"Validation failed: Unsupported unit {unit}")
                return False

            return True

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    async def execute_calculation(self, event_id: str, verified_data: Dict[str, Any], user_id: str) -> Optional[CalculationLedger]:
        """
        Executes the calculation pipeline:
        1. Calls CalculationService
        2. Creates EmissionEvent + CalculationLedger
        3. Resolves FlaggedEvent (if linked)
        """
        try:
            flagged_event = None
            if event_id:
                try:
                    uuid_event_id = UUID(event_id)
                    result = await self.db.execute(select(FlaggedEvent).where(FlaggedEvent.id == uuid_event_id))
                    flagged_event = result.scalars().first()
                except ValueError:
                    pass

            org_id = verified_data.get("organization_id")
            if not org_id and flagged_event:
                org_id = flagged_event.organization_id
            
            if not org_id:
                raise ValueError("Organization ID is required for calculation")

            # 1. Construct StandardizedEmissionEvent
            std_event = StandardizedEmissionEvent(
                event_id=event_id or str(uuid.uuid4()),
                org_id=org_id,
                timestamp=datetime.now(timezone.utc),
                activity_type=verified_data.get("activity_type", "electricity"),
                activity_value=float(verified_data["activity_value"]),
                activity_unit=verified_data["activity_unit"],
                location=LocationData(),
                data_quality=DataQuality(
                    source_type="user_entry",
                    confidence_score=1.0
                )
            )

            # 2. Calculate
            result: EmissionResult = await CalculationService.calculate_emissions(self.db, std_event)

            # 3. Create EmissionEvent
            emission_event = EmissionEvent(
                organization_id=org_id,
                activity_date=std_event.timestamp,
                activity_value=std_event.activity_value,
                activity_unit_raw=std_event.activity_unit,
                activity_unit_normalized=std_event.activity_unit, # simplified
                activity_value_normalized=std_event.activity_value,
                source_type="user_entry",
                scope="Scope 2", # default for MVp if type is electricity
                activity_id_matched=result.factor_used.get("activity_id"),
                confidence_score=1.0
            )
            self.db.add(emission_event)
            await self.db.flush()

            # 4. Create CalculationLedger
            # Get emission factor uuid
            ef_id = None
            if result.factor_used.get("id"):
                ef_id = result.factor_used.get("id")
            else:
                # Need to find or create a factor placeholder
                ef_res = await self.db.execute(select(EmissionFactor).limit(1))
                ef = ef_res.scalars().first()
                ef_id = ef.id if ef else uuid.uuid4()

            ledger = CalculationLedger(
                organization_id=org_id,
                emission_event_id=emission_event.id,
                activity_value=std_event.activity_value,
                activity_unit_normalized=std_event.activity_unit,
                emission_factor_id=ef_id,
                emission_factor_value=result.factor_used.get("value", 0.0),
                result_kg_co2e=result.location_based_co2e_kg,
                result_kg_total=result.location_based_co2e_kg,
                fell_back_to_climatiq=(result.calculation_method == "climatiq_api_latest"),
                calculated_by_user_id=UUID(user_id) if isinstance(user_id, str) else user_id
            )
            self.db.add(ledger)

            # 5. Resolve FlaggedEvent
            if flagged_event:
                flagged_event.status = "resolved"
                flagged_event.resolved_at = datetime.now(timezone.utc)
                flagged_event.resolved_by_user_id = user_id
                flagged_event.resolution_notes = f"Resolved by Analyst Agent with value {std_event.activity_value} {std_event.activity_unit}"

            await self.db.commit()
            await self.db.refresh(ledger)
            
            return ledger

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Analyst execution failed: {e}")
            raise
