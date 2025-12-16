"""
Integration Service - US-3.1, US-3.2
Handles OAuth integrations with AWS and QuickBooks
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import asyncio
import json

import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for external integrations (US-3.1, US-3.2)"""
    
    def __init__(self):
        """Initialize Gemini for data extraction"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def extract_aws_billing_data(self, billing_json: Dict) -> List[Dict]:
        """
        Extract AWS billing data and convert to emission transactions
        
        US-3.1 AC:
        - AWS connection established with OAuth
        - New cloud data syncs daily without human intervention
        - All synced data correctly identified as Scope 2
        - Entire sync process completes in under 5 minutes
        
        Args:
            billing_json: AWS Cost Explorer API response
            
        Returns:
            List of emission transaction dictionaries
        """
        transactions = []
        
        # Parse AWS billing structure
        if "ResultsByTime" in billing_json:
            for time_period in billing_json["ResultsByTime"]:
                start_date = time_period.get("TimePeriod", {}).get("Start")
                
                if "Groups" in time_period:
                    for group in time_period["Groups"]:
                        service_name = group.get("Keys", ["Unknown"])[0]
                        metrics = group.get("Metrics", {})
                        
                        # Extract usage and cost
                        usage_quantity = float(metrics.get("UsageQuantity", {}).get("Amount", 0))
                        cost = float(metrics.get("UnblendedCost", {}).get("Amount", 0))
                        
                        if usage_quantity > 0:
                            # Map AWS service to emission factor
                            emission_data = await self._map_aws_service_to_factor(
                                service_name,
                                usage_quantity,
                                billing_json.get("region", "us-east-1")
                            )
                            
                            transactions.append({
                                "description": f"AWS {service_name} Usage",
                                "transaction_date": start_date,
                                "scope": 2,  # All AWS usage is Scope 2
                                "category": "Purchased Electricity",
                                "activity_value": emission_data["activity_value"],
                                "activity_unit": emission_data["activity_unit"],
                                "emission_factor_value": emission_data["factor"],
                                "supplier_name": "Amazon Web Services",
                                "notes": f"Auto-synced from AWS. Service: {service_name}, Cost: ${cost:.2f}"
                            })
        
        logger.info(f"Extracted {len(transactions)} AWS transactions")
        return transactions
    
    async def _map_aws_service_to_factor(
        self,
        service_name: str,
        usage_quantity: float,
        region: str
    ) -> Dict:
        """Map AWS service to emission factor using Gemini"""
        
        prompt = f"""
        You are an AWS carbon accounting expert. Map this AWS service to appropriate emission calculation.
        
        **Service Details:**
        - Service: {service_name}
        - Usage Quantity: {usage_quantity}
        - Region: {region}
        
        **Task:**
        1. Determine the activity type (compute, storage, data transfer, etc.)
        2. Estimate kWh consumption based on typical service usage
        3. Select appropriate emission factor for the AWS region
        
        **Region Emission Factors (kg CO2e/kWh):**
        - us-east-1: 0.386
        - us-west-1: 0.298
        - eu-west-1: 0.255
        - Default: 0.386
        
        Return ONLY this JSON format:
        {{
            "activity_value": <estimated kWh>,
            "activity_unit": "kwh",
            "factor": <emission factor>,
            "reasoning": "<brief explanation>"
        }}
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            result_text = response.text.strip()
            
            # Clean JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()
            
            data = json.loads(result_text)
            return data
            
        except Exception as e:
            logger.error(f"AWS mapping failed: {str(e)}")
            # Fallback defaults
            return {
                "activity_value": usage_quantity * 0.1,  # Rough estimate
                "activity_unit": "kwh",
                "factor": 0.386,
                "reasoning": "Fallback estimate"
            }
    
    async def extract_quickbooks_transactions(self, qb_data: List[Dict]) -> List[Dict]:
        """
        Extract QuickBooks transactions and classify them
        
        US-3.2 AC:
        - QuickBooks connection established with OAuth
        - New transactions sync daily without manual intervention
        - AI classifies 80% or more automatically
        - Low-confidence items flagged for manual review
        - Entire sync process completes in under 5 minutes
        
        Args:
            qb_data: QuickBooks API response (list of transactions)
            
        Returns:
            List of emission transaction dictionaries
        """
        transactions = []
        
        for qb_tx in qb_data:
            # Extract transaction details
            description = qb_tx.get("Description", "") or qb_tx.get("EntityRef", {}).get("name", "Unknown")
            amount = float(qb_tx.get("TotalAmt", 0))
            date = qb_tx.get("TxnDate", datetime.now(timezone.utc).date().isoformat())
            vendor = qb_tx.get("EntityRef", {}).get("name", "")
            category = qb_tx.get("AccountRef", {}).get("name", "General")
            
            if amount > 0:
                # Use Gemini to classify and estimate emissions
                emission_data = await self._classify_qb_transaction(
                    description=description,
                    amount=amount,
                    vendor=vendor,
                    category=category
                )
                
                transactions.append({
                    "description": description,
                    "transaction_date": date,
                    "scope": emission_data["scope"],
                    "category": emission_data["category"],
                    "activity_value": emission_data["activity_value"],
                    "activity_unit": emission_data["activity_unit"],
                    "emission_factor_value": emission_data["factor"],
                    "supplier_name": vendor,
                    "ai_scope_prediction": emission_data["scope"],
                    "ai_confidence_score": emission_data["confidence"],
                    "ai_needs_review": emission_data["confidence"] < 0.8,
                    "notes": f"Auto-synced from QuickBooks. {emission_data['reasoning']}"
                })
        
        logger.info(f"Extracted {len(transactions)} QuickBooks transactions")
        return transactions
    
    async def _classify_qb_transaction(
        self,
        description: str,
        amount: float,
        vendor: str,
        category: str
    ) -> Dict:
        """Classify QuickBooks transaction using Gemini with function calling"""
        
        # Define tools for Gemini function calling
        tools = [
            {
                "name": "estimate_fuel_emissions",
                "description": "Estimate emissions from fuel purchases based on dollar amount",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount_usd": {"type": "number", "description": "Purchase amount in USD"},
                        "fuel_type": {"type": "string", "enum": ["gasoline", "diesel", "natural_gas", "propane"]},
                    },
                    "required": ["amount_usd", "fuel_type"]
                }
            },
            {
                "name": "estimate_electricity_emissions",
                "description": "Estimate emissions from electricity bills",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount_usd": {"type": "number", "description": "Bill amount in USD"},
                        "rate_per_kwh": {"type": "number", "description": "Average rate per kWh", "default": 0.12}
                    },
                    "required": ["amount_usd"]
                }
            },
            {
                "name": "estimate_travel_emissions",
                "description": "Estimate emissions from business travel",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount_usd": {"type": "number"},
                        "travel_type": {"type": "string", "enum": ["air", "rail", "taxi", "hotel"]}
                    },
                    "required": ["amount_usd", "travel_type"]
                }
            }
        ]
        
        prompt = f"""
        You are a carbon accounting expert. Classify this expense transaction.
        
        **Transaction:**
        - Description: {description}
        - Amount: ${amount}
        - Vendor: {vendor}
        - Category: {category}
        
        **Instructions:**
        1. Determine Scope (1, 2, or 3) per GHG Protocol
        2. Identify emission category
        3. Use available tools to estimate emissions
        4. Provide confidence score (0.0-1.0)
        
        Return ONLY this JSON format:
        {{
            "scope": <1, 2, or 3>,
            "category": "<emission category>",
            "activity_value": <estimated quantity>,
            "activity_unit": "<unit>",
            "factor": <emission factor kg CO2e per unit>,
            "confidence": <0.0 to 1.0>,
            "reasoning": "<brief explanation>"
        }}
        """
        
        try:
            # Use Gemini with function calling capability
            response = await self.model.generate_content_async(
                prompt,
                tools=tools
            )
            
            result_text = response.text.strip()
            
            # Clean JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()
            
            data = json.loads(result_text)
            
            # Ensure required fields
            if "scope" not in data or "confidence" not in data:
                raise ValueError("Missing required fields in response")
            
            return data
            
        except Exception as e:
            logger.error(f"QB classification failed: {str(e)}")
            # Fallback to Scope 3 with low confidence
            return {
                "scope": 3,
                "category": "Purchased Goods and Services",
                "activity_value": amount,
                "activity_unit": "usd",
                "factor": 0.5,  # Rough average
                "confidence": 0.5,
                "reasoning": "Fallback estimate due to classification error"
            }
