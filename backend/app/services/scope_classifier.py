"""
Scope classification service
Automatically classifies activities into Scope 1, 2, or 3
"""

from typing import Optional


class ScopeClassifier:
    """
    Automatic scope classification based on activity type
    
    Scopes:
    - Scope 1: Direct emissions from owned/controlled sources (fuel combustion)
    - Scope 2: Indirect emissions from purchased energy (electricity, heat, steam)
    - Scope 3: All other indirect emissions in value chain (travel, freight, procurement)
    """
    
    @staticmethod
    def classify(
        activity_type: str,
        sub_type: Optional[str] = None
    ) -> str:
        """
        Classify activity into appropriate GHG Protocol scope
        
        Args:
            activity_type: Primary activity category
            sub_type: Activity subcategory
            
        Returns:
            Scope classification: "Scope 1", "Scope 2", or "Scope 3"
            
        Examples:
            >>> ScopeClassifier.classify("energy", "fuel")
            'Scope 1'
            
            >>> ScopeClassifier.classify("energy", "electricity")
            'Scope 2'
            
            >>> ScopeClassifier.classify("travel")
            'Scope 3'
        """
        # Normalize inputs
        activity_type = activity_type.lower()
        sub_type = sub_type.lower() if sub_type else None
        
        # Scope 1: Direct emissions from owned sources
        if activity_type == "energy" and sub_type in ["fuel", "combustion", "natural_gas", "diesel", "gasoline", "propane"]:
            return "Scope 1"
        
        # Scope 2: Purchased energy
        if activity_type == "energy" and sub_type in ["electricity", "heat", "steam", "cooling"]:
            return "Scope 2"
        
        # Scope 3: Value chain emissions
        if activity_type in [
            "travel",
            "freight",
            "procurement",
            "waste",
            "water",
            "business_travel",
            "employee_commuting",
            "upstream_transport",
            "downstream_transport"
        ]:
            return "Scope 3"
        
        # Default to Scope 3 for unknown categories
        return "Scope 3"
    
    @staticmethod
    def get_scope_3_category(activity_type: str, sub_type: Optional[str] = None) -> Optional[str]:
        """
        Get specific Scope 3 category number
        
        Args:
            activity_type: Primary activity category
            sub_type: Activity subcategory
            
        Returns:
            Scope 3 category (e.g., "3.6 - Business Travel") or None
        """
        mapping = {
            ("travel", "business"): "3.6 - Business Travel",
            ("travel", "employee_commuting"): "3.7 - Employee Commuting",
            ("freight", "upstream"): "3.4 - Upstream Transportation",
            ("freight", "downstream"): "3.9 - Downstream Transportation",
            ("procurement", None): "3.1 - Purchased Goods and Services",
            ("waste", None): "3.5 - Waste Generated in Operations",
            ("water", None): "3.1 - Purchased Goods and Services"
        }
        
        return mapping.get((activity_type, sub_type))
    
    @staticmethod
    def validate_scope(scope: str) -> bool:
        """
        Validate scope string
        
        Args:
            scope: Scope string to validate
            
        Returns:
            True if valid scope
        """
        valid_scopes = ["Scope 1", "Scope 2", "Scope 3"]
        return scope in valid_scopes
    
    @staticmethod
    def get_scope_description(scope: str) -> str:
        """
        Get human-readable scope description
        
        Args:
            scope: Scope identifier
            
        Returns:
            Description of the scope
        """
        descriptions = {
            "Scope 1": "Direct GHG emissions from owned or controlled sources",
            "Scope 2": "Indirect GHG emissions from the generation of purchased energy",
            "Scope 3": "All other indirect emissions in the value chain"
        }
        
        return descriptions.get(scope, "Unknown scope")


# Global classifier instance
scope_classifier = ScopeClassifier()
