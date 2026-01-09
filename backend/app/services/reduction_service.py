"""
Reduction Service
Manages reduction targets and generates AI-powered reduction strategies
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.reduction_target import ReductionTarget
from app.models.reduction_strategy import ReductionStrategy
from app.models.activity import EmissionActivity
from app.models.organization import Organization
from app.services.groq_service import GroqService
from app.core.archetype_config import get_archetype

logger = logging.getLogger(__name__)


class ReductionService:
    """
    Service for managing reduction targets and generating AI strategies
    
    Features:
    - Target CRUD with progress calculation
    - Archetype-specific AI strategy generation
    - 7-day strategy caching to respect rate limits
    """
    
    def __init__(self, db: Session, organization_id: UUID):
        self.db = db
        self.organization_id = organization_id
        self.groq_service = GroqService()
        self._organization = None
    
    @property
    def organization(self) -> Organization:
        """Lazy load organization"""
        if self._organization is None:
            self._organization = self.db.query(Organization).filter(
                Organization.id == self.organization_id
            ).first()
        return self._organization
    
    @property
    def archetype(self) -> Optional[str]:
        """Get organization's archetype"""
        return self.organization.emission_archetype if self.organization else None
    
    # ==================== Target CRUD ====================
    
    def create_target(
        self,
        name: str,
        target_type: str,
        baseline_year: str,
        baseline_value: float,
        target_year: str,
        target_value: float,
        scope: Optional[str] = "all",
        description: Optional[str] = None,
        milestones: Optional[List[Dict]] = None,
        project_id: Optional[UUID] = None
    ) -> ReductionTarget:
        """Create a new reduction target"""
        
        target = ReductionTarget(
            organization_id=self.organization_id,
            project_id=project_id,
            name=name,
            description=description,
            target_type=target_type,
            scope=scope,
            baseline_year=baseline_year,
            baseline_value=Decimal(str(baseline_value)),
            target_year=target_year,
            target_value=Decimal(str(target_value)),
            milestones=milestones or [],
            status="on_track",
            is_active=True
        )
        
        self.db.add(target)
        self.db.commit()
        self.db.refresh(target)
        
        # Calculate initial progress
        self.update_target_progress(target.id)
        
        logger.info(f"Created reduction target: {name} for org {self.organization_id}")
        return target
    
    def get_targets(self, active_only: bool = True) -> List[ReductionTarget]:
        """Get all reduction targets for the organization"""
        query = self.db.query(ReductionTarget).filter(
            ReductionTarget.organization_id == self.organization_id
        )
        
        if active_only:
            query = query.filter(ReductionTarget.is_active == True)
        
        return query.order_by(ReductionTarget.created_at.desc()).all()
    
    def get_target(self, target_id: UUID) -> Optional[ReductionTarget]:
        """Get a specific target"""
        return self.db.query(ReductionTarget).filter(
            ReductionTarget.id == target_id,
            ReductionTarget.organization_id == self.organization_id
        ).first()
    
    def update_target(
        self,
        target_id: UUID,
        **kwargs
    ) -> Optional[ReductionTarget]:
        """Update a reduction target"""
        target = self.get_target(target_id)
        if not target:
            return None
        
        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'target_type', 'scope',
            'baseline_year', 'baseline_value', 'target_year', 'target_value',
            'milestones', 'is_active'
        ]
        
        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                if field in ['baseline_value', 'target_value']:
                    setattr(target, field, Decimal(str(kwargs[field])))
                else:
                    setattr(target, field, kwargs[field])
        
        self.db.commit()
        self.db.refresh(target)
        
        # Recalculate progress after update
        self.update_target_progress(target_id)
        
        return target
    
    def delete_target(self, target_id: UUID) -> bool:
        """Soft delete a target (set inactive)"""
        target = self.get_target(target_id)
        if not target:
            return False
        
        target.is_active = False
        self.db.commit()
        return True
    
    # ==================== Progress Calculation ====================
    
    def update_target_progress(self, target_id: UUID) -> Optional[ReductionTarget]:
        """Calculate and update progress for a target"""
        target = self.get_target(target_id)
        if not target:
            return None
        
        # Get current emissions for the relevant scope
        current_emissions = self._get_current_emissions(target.scope, target.project_id)
        
        if current_emissions is not None:
            # Use the model's calculation method
            progress_data = target.calculate_progress(Decimal(str(current_emissions)))
            
            target.current_value = Decimal(str(current_emissions))
            target.current_year = str(datetime.now().year)
            target.progress_percentage = Decimal(str(progress_data['progress_percentage']))
            target.current_reduction_pct = Decimal(str(progress_data['current_reduction_pct']))
            target.status = progress_data['status']
            target.last_calculated_at = datetime.utcnow()
            
            # Update milestone achievements
            self._update_milestone_achievements(target)
            
            self.db.commit()
            self.db.refresh(target)
        
        return target
    
    def update_all_targets_progress(self) -> int:
        """Update progress for all active targets"""
        targets = self.get_targets(active_only=True)
        updated = 0
        
        for target in targets:
            if self.update_target_progress(target.id):
                updated += 1
        
        return updated
    
    def _get_current_emissions(
        self, 
        scope: Optional[str], 
        project_id: Optional[UUID]
    ) -> Optional[float]:
        """Get current total emissions for scope"""
        query = self.db.query(func.sum(EmissionActivity.co2e_kg)).join(
            EmissionActivity.project
        ).filter(
            EmissionActivity.project.has(organization_id=self.organization_id)
        )
        
        if project_id:
            query = query.filter(EmissionActivity.project_id == project_id)
        
        if scope and scope != "all":
            query = query.filter(EmissionActivity.scope == scope)
        
        result = query.scalar()
        return float(result) if result else None
    
    def _update_milestone_achievements(self, target: ReductionTarget) -> None:
        """Update milestone achievement status based on current progress"""
        if not target.milestones or not target.current_reduction_pct:
            return
        
        updated_milestones = []
        for milestone in target.milestones:
            milestone_value = milestone.get('value', 0)
            
            # Check if milestone is achieved
            if target.current_reduction_pct >= Decimal(str(milestone_value)):
                milestone['achieved'] = True
                if not milestone.get('achieved_at'):
                    milestone['achieved_at'] = datetime.utcnow().isoformat()
            else:
                milestone['achieved'] = False
                milestone['achieved_at'] = None
            
            updated_milestones.append(milestone)
        
        target.milestones = updated_milestones
    
    # ==================== AI Strategy Generation ====================
    
    async def generate_strategies(
        self,
        target_id: UUID,
        force_refresh: bool = False,
        max_strategies: int = 5
    ) -> List[ReductionStrategy]:
        """
        Generate AI-powered reduction strategies
        
        Rate-limit conscious:
        - Check cache first (by prompt_hash)
        - Use llama-3.3-70b-versatile (quality model)
        - Cache result for 7 days
        """
        target = self.get_target(target_id)
        if not target:
            return []
        
        # Build cache key
        cache_key = self._build_strategy_cache_key(target)
        
        # Check cache unless force refresh
        if not force_refresh:
            cached_strategies = self._get_cached_strategies(cache_key)
            if cached_strategies:
                logger.info(f"Returning cached strategies for target {target_id}")
                return cached_strategies
        
        # Generate new strategies via Groq (70b model)
        try:
            strategies_data = await self._call_groq_for_strategies(target, max_strategies)
            
            # Persist strategies with cache
            strategies = self._persist_strategies(
                target_id=target_id,
                strategies_data=strategies_data,
                cache_key=cache_key
            )
            
            logger.info(f"Generated {len(strategies)} strategies for target {target_id}")
            return strategies
            
        except Exception as e:
            logger.error(f"Failed to generate strategies: {e}")
            # Return empty list - don't fail the request
            return []
    
    def get_strategies(self, target_id: Optional[UUID] = None) -> List[ReductionStrategy]:
        """Get strategies for a target or all org strategies"""
        query = self.db.query(ReductionStrategy).filter(
            ReductionStrategy.organization_id == self.organization_id
        )
        
        if target_id:
            query = query.filter(ReductionStrategy.target_id == target_id)
        
        # Only return non-expired strategies
        query = query.filter(
            (ReductionStrategy.expires_at == None) | 
            (ReductionStrategy.expires_at > datetime.utcnow())
        )
        
        return query.order_by(ReductionStrategy.priority).all()
    
    def _build_strategy_cache_key(self, target: ReductionTarget) -> str:
        """Build hash key for strategy caching"""
        context = {
            "org_id": str(self.organization_id),
            "target_id": str(target.id),
            "archetype": self.archetype,
            "scope": target.scope,
            "target_type": target.target_type,
            "target_value": str(target.target_value),
            "current_value": str(target.current_value) if target.current_value else "0"
        }
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.sha256(context_str.encode()).hexdigest()
    
    def _get_cached_strategies(self, cache_key: str) -> Optional[List[ReductionStrategy]]:
        """Check cache for existing strategies"""
        strategies = self.db.query(ReductionStrategy).filter(
            ReductionStrategy.organization_id == self.organization_id,
            ReductionStrategy.prompt_hash == cache_key,
            ReductionStrategy.expires_at > datetime.utcnow()
        ).order_by(ReductionStrategy.priority).all()
        
        return strategies if strategies else None
    
    async def _call_groq_for_strategies(
        self, 
        target: ReductionTarget,
        max_strategies: int
    ) -> List[Dict[str, Any]]:
        """Call Groq 70b model for strategy generation"""
        
        # Get archetype fingerprint for context
        archetype_info = get_archetype(self.archetype) if self.archetype else None
        
        # Build detailed prompt
        prompt = self._build_strategy_prompt(target, archetype_info, max_strategies)
        
        # Call Groq with quality model
        response = await self.groq_service.generate_strategies(
            prompt=prompt,
            use_quality_model=True
        )
        
        return response.get('strategies', [])
    
    def _build_strategy_prompt(
        self, 
        target: ReductionTarget, 
        archetype_info: Optional[Any],
        max_strategies: int
    ) -> str:
        """Build prompt for strategy generation"""
        
        archetype_context = ""
        if archetype_info:
            archetype_context = f"""
Organization Archetype: {archetype_info.display_name}
Industries: {', '.join(archetype_info.corresponding_industries)}
Expected Activity Types: {', '.join(archetype_info.expected_activity_types)}
Key Emission Signals: {', '.join(archetype_info.key_emission_signals)}
"""
        
        return f"""You are a Carbon Reduction Strategy Expert. Generate specific, actionable reduction strategies for this organization.

{archetype_context}

Target Details:
- Name: {target.name}
- Type: {target.target_type} ({'percentage reduction' if target.is_percentage_target else 'absolute target'})
- Scope: {target.scope or 'All scopes'}
- Baseline ({target.baseline_year}): {target.baseline_value:,.0f} kg CO2e
- Target ({target.target_year}): {target.target_value}{'%' if target.is_percentage_target else ' kg CO2e'}
- Current Emissions: {target.current_value:,.0f} kg CO2e if target.current_value else 'Not calculated'
- Progress: {target.progress_percentage}% if target.progress_percentage else 'N/A'

Generate {max_strategies} specific, prioritized reduction strategies tailored to this organization's archetype and target.

Return ONLY valid JSON in this format:
{{
    "strategies": [
        {{
            "title": "Brief action title",
            "description": "Detailed explanation of the strategy and how to implement it",
            "category": "energy|travel|procurement|operations|facility",
            "scope": "Scope 1|Scope 2|Scope 3",
            "estimated_reduction_pct": 5.0,
            "difficulty": "easy|medium|hard",
            "implementation_timeframe": "immediate|short-term|medium-term|long-term",
            "priority": 1
        }}
    ]
}}

Prioritize by impact and feasibility. Be specific to the organization type."""
    
    def _persist_strategies(
        self,
        target_id: UUID,
        strategies_data: List[Dict[str, Any]],
        cache_key: str
    ) -> List[ReductionStrategy]:
        """Persist generated strategies with cache metadata"""
        
        # Delete old cached strategies for this cache key
        self.db.query(ReductionStrategy).filter(
            ReductionStrategy.organization_id == self.organization_id,
            ReductionStrategy.prompt_hash == cache_key
        ).delete()
        
        strategies = []
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        for i, data in enumerate(strategies_data):
            strategy = ReductionStrategy(
                organization_id=self.organization_id,
                target_id=target_id,
                title=data.get('title', f'Strategy {i+1}'),
                description=data.get('description', ''),
                category=data.get('category', 'operations'),
                scope=data.get('scope'),
                archetype=self.archetype,
                estimated_reduction_pct=data.get('estimated_reduction_pct'),
                difficulty=data.get('difficulty', 'medium'),
                priority=data.get('priority', i + 1),
                implementation_timeframe=data.get('implementation_timeframe', 'medium-term'),
                model_used="llama-3.3-70b-versatile",
                prompt_hash=cache_key,
                source="ai",
                expires_at=expires_at,
                status="suggested"
            )
            self.db.add(strategy)
            strategies.append(strategy)
        
        self.db.commit()
        
        for strategy in strategies:
            self.db.refresh(strategy)
        
        return strategies
    
    def update_strategy_status(
        self, 
        strategy_id: UUID, 
        status: str
    ) -> Optional[ReductionStrategy]:
        """Update strategy status (considering, in_progress, completed, rejected)"""
        strategy = self.db.query(ReductionStrategy).filter(
            ReductionStrategy.id == strategy_id,
            ReductionStrategy.organization_id == self.organization_id
        ).first()
        
        if strategy:
            strategy.status = status
            self.db.commit()
            self.db.refresh(strategy)
        
        return strategy


def create_reduction_service(db: Session, organization_id: UUID) -> ReductionService:
    """Factory function for ReductionService"""
    return ReductionService(db, organization_id)
