"""
DSPy-based multi-agent system for emissions classification
- ScopeClassifier: Predicts Scope 1, 2, or 3
- FactorMatcher: Finds emission factor
- Validator: Checks reasonableness
- MultiAgentClassifier: Orchestrates all agents
"""

import dspy
from typing import Optional, Dict
from pydantic import BaseModel
import logging
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)

# Scope definitions for agents
SCOPE_DEFINITIONS = {
    1: "Direct emissions from company operations (gas heating, vehicle fuel, refrigerants)",
    2: "Indirect emissions from purchased electricity, steam, or heating",
    3: "Indirect emissions from supply chain, business travel, waste"
}

CATEGORY_TO_SCOPE_HINTS = {
    "Fuel": 1,  # Scope 1
    "Natural Gas": 1,
    "Gasoline": 1,
    "Diesel": 1,
    "Electricity": 2,  # Scope 2
    "Power": 2,
    "Business Travel": 3,  # Scope 3
    "Air Travel": 3,
    "Shipping": 3,
    "Supplier": 3,
    "Waste": 3
}

# ==================== Initialize Gemini ====================

def init_gemini_lm(api_key: str, model: str = "gemini-2.0-flash"):
    """Initialize Google Gemini as LM for DSPy"""
    try:
        lm = dspy.Google(
            api_key=api_key,
            model=model,
            temperature=0.3,  # Low = deterministic
            max_tokens=150
        )
        dspy.settings.configure(lm=lm)
        logger.info(f"Initialized Gemini LM: {model}")
        return lm
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {str(e)}")
        raise

# ==================== Agent Signatures ====================

class ScopeClassifierSignature(dspy.Signature):
    """Classify transaction into Scope 1, 2, or 3"""
    
    description: str = dspy.InputField(
        desc="Transaction/expense description (e.g., 'Purchased 100 kWh of electricity')"
    )
    category: str = dspy.InputField(
        desc="Expense category (e.g., Fuel, Electricity, Business Travel, Shipping)"
    )
    
    scope: int = dspy.OutputField(
        desc="Scope 1 (direct), 2 (purchased electricity), or 3 (indirect). Respond with 1, 2, or 3 only."
    )
    reasoning: str = dspy.OutputField(
        desc="Why you chose this scope"
    )
    confidence: float = dspy.OutputField(
        desc="Confidence 0.0-1.0. High if clear, low if ambiguous"
    )

class FactorMatcherSignature(dspy.Signature):
    """Find the best emission factor for a transaction"""
    
    description: str = dspy.InputField(
        desc="Transaction description"
    )
    scope: int = dspy.InputField(
        desc="Scope (1, 2, or 3)"
    )
    category: str = dspy.InputField(
        desc="Expense category"
    )
    
    factor_unit: str = dspy.OutputField(
        desc="Unit for factor (e.g., kg CO2e/kWh, kg CO2e/liter, kg CO2e/km)"
    )
    factor_value: float = dspy.OutputField(
        desc="Numeric value of emission factor (typical ranges: 0.1-1.0 for electricity, 2-3 for fuel)"
    )
    source: str = dspy.OutputField(
        desc="Source of factor (e.g., EPA, DEFRA, IVL)"
    )
    confidence: float = dspy.OutputField(
        desc="Confidence in factor selection (0.0-1.0)"
    )

class ValidatorSignature(dspy.Signature):
    """Validate that classification and factor are reasonable"""
    
    description: str = dspy.InputField(
        desc="Transaction description"
    )
    scope: int = dspy.InputField(
        desc="Predicted scope"
    )
    category: str = dspy.InputField(
        desc="Category"
    )
    factor_value: float = dspy.InputField(
        desc="Emission factor value"
    )
    
    is_reasonable: bool = dspy.OutputField(
        desc="True if classification seems reasonable, False if suspicious"
    )
    issues: str = dspy.OutputField(
        desc="Any issues found (empty if OK)"
    )
    confidence: float = dspy.OutputField(
        desc="Confidence in validation (0.0-1.0)"
    )

# ==================== Agent Classes ====================

class ScopeClassifier(dspy.ChainOfThought):
    """Chain-of-thought classifier for Scope prediction"""
    pass

class FactorMatcher(dspy.ChainOfThought):
    """Find appropriate emission factor"""
    pass

class Validator(dspy.ChainOfThought):
    """Validate scope and factor"""
    pass

# ==================== Multi-Agent Orchestrator ====================

class MultiAgentClassifier:
    """Main orchestrator for multi-agent classification system"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        """Initialize classifier with all agents"""
        try:
            init_gemini_lm(api_key, model)
            
            # Create agent instances
            self.scope_classifier = ScopeClassifier(ScopeClassifierSignature)
            self.factor_matcher = FactorMatcher(FactorMatcherSignature)
            self.validator = Validator(ValidatorSignature)
            
            logger.info("MultiAgentClassifier initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize classifier: {str(e)}")
            raise
    
    def classify(
        self,
        transaction_id: str,
        description: str,
        category: str,
        activity_value: float = 1.0
    ) -> Dict:
        """
        Classify transaction through multi-agent pipeline
        
        Args:
            transaction_id: Unique transaction ID
            description: Transaction description
            category: Expense category
            activity_value: Amount of activity (for CO2e calculation)
        
        Returns:
            {
                'transaction_id': str,
                'scope': int (1, 2, or 3),
                'confidence': float (0.0-1.0),
                'needs_review': bool,
                'factor_value': float,
                'factor_unit': str,
                'co2e_kg': float,
                'reasoning': dict with detailed info
            }
        """
        
        logger.info(f"Classifying TX {transaction_id}: '{description}'")
        
        try:
            # STEP 1: Classify Scope
            logger.debug("Step 1: Running Scope Classifier...")
            scope_result = self.scope_classifier.forward(
                description=description,
                category=category
            )
            
            scope = self._parse_scope(scope_result.scope)
            scope_confidence = self._parse_confidence(scope_result.confidence)
            scope_reasoning = str(scope_result.reasoning)
            
            logger.debug(f"  Scope: {scope}, Confidence: {scope_confidence:.2f}")
            
            # STEP 2: Match Factor
            logger.debug("Step 2: Running Factor Matcher...")
            factor_result = self.factor_matcher.forward(
                description=description,
                scope=scope,
                category=category
            )
            
            factor_value = float(factor_result.factor_value)
            factor_unit = str(factor_result.factor_unit)
            factor_confidence = self._parse_confidence(factor_result.confidence)
            
            logger.debug(f"  Factor: {factor_value} {factor_unit}, Confidence: {factor_confidence:.2f}")
            
            # STEP 3: Validate
            logger.debug("Step 3: Running Validator...")
            validator_result = self.validator.forward(
                description=description,
                scope=scope,
                category=category,
                factor_value=factor_value
            )
            
            is_reasonable = self._parse_bool(validator_result.is_reasonable)
            validation_issues = str(validator_result.issues)
            validator_confidence = self._parse_confidence(validator_result.confidence)
            
            logger.debug(f"  Reasonable: {is_reasonable}, Confidence: {validator_confidence:.2f}")
            
            # STEP 4: Aggregate Confidence
            combined_confidence = self._aggregate_confidence(
                scope_confidence,
                factor_confidence,
                validator_confidence
            )
            
            # STEP 5: Determine if needs review
            needs_review = combined_confidence < 0.80
            
            # STEP 6: Calculate CO2e
            co2e_kg = activity_value * factor_value
            
            result = {
                'transaction_id': transaction_id,
                'scope': scope,
                'confidence': round(combined_confidence, 3),
                'needs_review': needs_review,
                'factor_value': round(factor_value, 4),
                'factor_unit': factor_unit,
                'co2e_kg': round(co2e_kg, 3),
                'reasoning': {
                    'scope_reasoning': scope_reasoning,
                    'is_reasonable': is_reasonable,
                    'validation_issues': validation_issues,
                    'agent_confidences': {
                        'scope': round(scope_confidence, 3),
                        'factor': round(factor_confidence, 3),
                        'validator': round(validator_confidence, 3)
                    }
                }
            }
            
            logger.info(
                f"Classification complete - TX: {transaction_id}, "
                f"Scope: {scope}, Confidence: {combined_confidence:.2f}, "
                f"Review: {needs_review}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Classification error for TX {transaction_id}: {str(e)}")
            return {
                'transaction_id': transaction_id,
                'scope': 1,
                'confidence': 0.0,
                'needs_review': True,
                'factor_value': 0.0,
                'factor_unit': 'unknown',
                'co2e_kg': 0.0,
                'error': str(e),
                'reasoning': {
                    'scope_reasoning': 'Error in classification',
                    'is_reasonable': False,
                    'validation_issues': str(e)
                }
            }
    
    # ==================== Helper Methods ====================
    
    @staticmethod
    def _parse_scope(scope_str) -> int:
        """Parse scope from LLM output"""
        try:
            scope = int(float(str(scope_str).strip()))
            return max(1, min(3, scope))  # Clamp to 1-3
        except:
            return 1
    
    @staticmethod
    def _parse_confidence(conf_str) -> float:
        """Parse confidence from LLM output"""
        try:
            conf = float(str(conf_str).strip())
            return max(0.0, min(1.0, conf))  # Clamp to 0-1
        except:
            return 0.0
    
    @staticmethod
    def _parse_bool(bool_str) -> bool:
        """Parse boolean from LLM output"""
        try:
            s = str(bool_str).lower().strip()
            return s in ['true', 'yes', '1', 'y']
        except:
            return False
    
    @staticmethod
    def _aggregate_confidence(
        scope_conf: float,
        factor_conf: float,
        validator_conf: float
    ) -> float:
        """
        Aggregate confidence from three agents with weights
        
        Weights:
        - Scope: 40% (most important for classification)
        - Factor: 30%
        - Validator: 30%
        """
        weights = [0.4, 0.3, 0.3]
        confidences = [
            max(0.0, scope_conf),
            max(0.0, factor_conf),
            max(0.0, validator_conf)
        ]
        
        aggregate = sum(w * c for w, c in zip(weights, confidences))
        return min(1.0, aggregate)
    
    def classify_batch(
        self,
        transactions: list
    ) -> list:
        """
        Classify multiple transactions
        
        Args:
            transactions: List of {'id', 'description', 'category', 'activity_value'}
        
        Returns:
            List of classification results
        """
        results = []
        for tx in transactions:
            result = self.classify(
                transaction_id=tx['id'],
                description=tx['description'],
                category=tx['category'],
                activity_value=tx.get('activity_value', 1.0)
            )
            results.append(result)
        
        return results