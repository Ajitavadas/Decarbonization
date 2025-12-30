"""
CRUD operations for Custom Mappings
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.custom_mapping import CustomMapping


class CRUDMapping(CRUDBase[CustomMapping]):
    """CRUD operations for custom ERP mappings"""
    
    def get_by_organization(
        self,
        db: Session,
        *,
        organization_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[CustomMapping]:
        """Get mappings for an organization"""
        return (
            db.query(self.model)
            .filter(CustomMapping.organization_id == organization_id)
            .order_by(CustomMapping.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_internal_label(
        self,
        db: Session,
        *,
        organization_id: str,
        internal_label: str
    ) -> Optional[CustomMapping]:
        """Get mapping by internal label"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    CustomMapping.organization_id == organization_id,
                    CustomMapping.internal_label == internal_label
                )
            )
            .first()
        )
    
    def get_by_category(
        self,
        db: Session,
        *,
        organization_id: str,
        category: str
    ) -> List[CustomMapping]:
        """Get mappings by category"""
        return (
            db.query(self.model)
            .filter(
                and_(
                    CustomMapping.organization_id == organization_id,
                    CustomMapping.category == category
                )
            )
            .all()
        )
    
    def increment_usage(
        self,
        db: Session,
        *,
        mapping_id: str
    ) -> CustomMapping:
        """Increment usage counter for a mapping"""
        mapping = self.get(db, id=mapping_id)
        if mapping:
            mapping.usage_count += 1
            mapping.last_used_at = datetime.utcnow()
            db.add(mapping)
            db.commit()
            db.refresh(mapping)
        return mapping
    
    def search(
        self,
        db: Session,
        *,
        organization_id: str,
        query: str
    ) -> List[CustomMapping]:
        """Search mappings by internal label or code"""
        search_term = f"%{query}%"
        return (
            db.query(self.model)
            .filter(
                and_(
                    CustomMapping.organization_id == organization_id,
                    (
                        CustomMapping.internal_label.ilike(search_term) |
                        CustomMapping.internal_code.ilike(search_term)
                    )
                )
            )
            .all()
        )


# Create CRUD instance
crud_mapping = CRUDMapping(CustomMapping)
