"""
Mistral OCR Service
Extracts structured activity data from PDF and image files using Mistral AI OCR API.
"""

import logging
import json
import base64
import traceback
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class MistralOCRService:
    """Service for extracting activity data from PDFs and images using Mistral OCR"""
    
    # Required fields for emission calculation
    REQUIRED_FIELDS = ["description", "amount", "unit", "region", "activity_date", "year", "category"]
    OPTIONAL_FIELDS = ["supplier_name"]
    
    def __init__(self):
        """Initialize Mistral OCR client"""
        self.api_key = settings.MISTRAL_API_KEY
        self.base_url = "https://api.mistral.ai/v1"
        self.timeout = httpx.Timeout(120.0, connect=15.0)  # Longer timeout for OCR and large documents
    
    async def extract_from_pdf(self, file_bytes: bytes, filename: str = "document.pdf") -> List[Dict[str, Any]]:
        """
        Extract structured activity data from a PDF file.
        
        Args:
            file_bytes: PDF file content as bytes
            filename: Original filename for context
            
        Returns:
            List of activity records with required fields
        """
        print(f"[PDF OCR] Starting extraction for: {filename} ({len(file_bytes)} bytes)")
        logger.info(f"Processing PDF: {filename} ({len(file_bytes)} bytes)")
        
        # Convert PDF to base64 for API
        pdf_base64 = base64.standard_b64encode(file_bytes).decode("utf-8")
        print(f"[PDF OCR] Converted to base64 ({len(pdf_base64)} chars)")
        
        # OCR the PDF using Mistral's document OCR endpoint
        try:
            ocr_result = await self._call_ocr_api(pdf_base64, filename)
            print(f"[PDF OCR] OCR result received: {len(ocr_result) if ocr_result else 0} chars")
            if ocr_result:
                print(f"[PDF OCR] OCR preview: {ocr_result[:500]}...")
        except Exception as e:
            print(f"[PDF OCR] OCR API call failed: {str(e)}")
            logger.error(f"OCR API call failed: {str(e)}")
            return []
        
        if not ocr_result:
            print(f"[PDF OCR] OCR returned empty result")
            logger.warning(f"OCR returned empty result for {filename}")
            return []
        
        # First try direct markdown table parsing (fast, no AI)
        activities = self._parse_markdown_table(ocr_result)
        
        # If direct parsing found activities, return them
        if activities:
            print(f"[PDF OCR] Direct parsing successful - extracted {len(activities)} activities")
            logger.info(f"Extracted {len(activities)} activities from {filename} via direct parsing")
            return activities
        
        # Fallback to AI extraction (slower, more flexible)
        print(f"[PDF OCR] Direct parsing found no activities, trying AI extraction...")
        try:
            activities = await self._parse_ocr_to_activities(ocr_result)
            print(f"[PDF OCR] AI extraction result: {len(activities)} activities")
        except Exception as e:
            print(f"[PDF OCR] AI activity parsing failed: {str(e)}")
            logger.error(f"AI activity parsing failed: {str(e)}")
            return []
        
        logger.info(f"Extracted {len(activities)} activities from {filename}")
        return activities
    
    async def extract_from_image(self, file_bytes: bytes, filename: str = "image.png") -> List[Dict[str, Any]]:
        """
        Extract structured activity data from an image file.
        
        Args:
            file_bytes: Image file content as bytes
            filename: Original filename for context
            
        Returns:
            List of activity records with required fields
        """
        logger.info(f"Processing image: {filename} ({len(file_bytes)} bytes)")
        
        # Determine MIME type
        extension = filename.lower().split('.')[-1]
        mime_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        mime_type = mime_types.get(extension, 'image/png')
        
        # Convert image to base64
        image_base64 = base64.standard_b64encode(file_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{image_base64}"
        
        # Use vision endpoint for image processing
        ocr_result = await self._call_vision_api(data_url)
        
        if not ocr_result:
            logger.warning(f"Vision API returned empty result for {filename}")
            return []
        
        # Parse the result to extract structured activity data
        activities = await self._parse_ocr_to_activities(ocr_result)
        
        logger.info(f"Extracted {len(activities)} activities from {filename}")
        return activities
    
    async def _call_ocr_api(self, pdf_base64: str, filename: str) -> str:
        """
        Call Mistral OCR API to extract text from PDF.
        
        Args:
            pdf_base64: Base64 encoded PDF
            filename: Original filename
            
        Returns:
            OCR result as markdown/text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Mistral OCR endpoint
        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}"
            },
            "include_image_base64": False
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/ocr",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract text content from OCR response
                pages = result.get("pages", [])
                all_text = []
                for page in pages:
                    markdown = page.get("markdown", "")
                    if markdown:
                        all_text.append(markdown)
                
                return "\n\n".join(all_text)
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Mistral OCR API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"OCR API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Mistral OCR API call failed: {str(e)}")
                raise
    
    async def _call_vision_api(self, image_data_url: str) -> str:
        """
        Call Mistral Vision API to extract text from image.
        
        Args:
            image_data_url: Data URL with base64 encoded image
            
        Returns:
            Extracted text content
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use chat completions with vision for images
        payload = {
            "model": "pixtral-12b-2409",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text and tabular data from this image. If there are tables, format them as markdown tables. Preserve the structure as much as possible."
                        },
                        {
                            "type": "image_url",
                            "image_url": image_data_url
                        }
                    ]
                }
            ],
            "max_tokens": 4096
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                choices = result.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Mistral Vision API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Vision API error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"Mistral Vision API call failed: {str(e)}")
                raise
    
    async def _parse_ocr_to_activities(self, ocr_content: str) -> List[Dict[str, Any]]:
        """
        Parse OCR output to extract structured activity records using AI.
        
        Args:
            ocr_content: OCR/vision output text (markdown or plain text)
            
        Returns:
            List of activity dictionaries with required fields
        """
        if not ocr_content or len(ocr_content.strip()) < 10:
            return []
        
        prompt = f"""You are an expert at extracting carbon emission activity data from documents.

Given the following document content (from OCR), extract ALL activity records that contain carbon emission relevant data.

Document Content:
{ocr_content}

COLUMN MAPPING - The document may use different column names. Map them as follows:
- description: May be called "Activity Description", "Activity", "Description", "Item", "Name", "Activity Name"
- amount: May be called "Consumption Value", "Value", "Amount", "Quantity", "Usage", "Consumption"
- unit: May be called "Unit", "Units", "UoM", "Unit of Measure", "Measurement"
- region: May be called "Location", "Region", "Location / Region", "Country", "Area", "State"
- activity_date/year: May be called "Time Period", "Period", "Date", "Month", "Year", "Reporting Period"
- category: Infer from description if not explicit (e.g., "electricity" → "Electricity", "travel" → "Business Travel")

REGION NORMALIZATION - Convert location names to ISO 3166-1 alpha-2 country codes ONLY:
- "Karnataka", "Maharashtra", "Delhi", any Indian state, "All India" → "IN"
- "California", "Texas", any US state → "US"
- "International" → "GLOBAL"
- United Kingdom, England, Scotland → "GB"
- Germany → "DE"
- China → "CN"
IMPORTANT: Always use 2-letter country codes (IN, US, GB, DE, etc.), never sub-national codes.

DATE PARSING - Handle various date formats:
- "January 2024" → "2024-01-15" (use 15th as mid-month)
- "Q1 2024" → "2024-02-15" (use mid-quarter)
- "Annual 2024" → "2024-07-01" (use mid-year)
- Extract year from any date format

For EACH activity row found, return:
{{
  "description": "Activity description text",
  "amount": 12345,
  "unit": "kWh or appropriate unit",
  "region": "ISO 3166-1 alpha-2 code (e.g., IN, US, GB)",
  "activity_date": "YYYY-MM-DD format",
  "year": 2024,
  "category": "Category name",
  "supplier_name": "Supplier if mentioned, otherwise null"
}}

IMPORTANT:
1. Extract EVERY row from tables - do not summarize or skip rows
2. Parse numeric values correctly (remove commas: "145,000" → 145000)
3. Infer category from description if not explicit:
   - "electricity" → "Electricity"
   - "diesel", "fuel", "LPG", "gas" → "Fuel"
   - "water" → "Water"
   - "travel", "flight", "air travel" → "Business Travel"
   - "freight", "transport", "courier" → "Freight"
   - "material", "purchase", "packaging" → "Procurement"
   - "employee commute" → "Employee Commute"
   - "hotel", "accommodation" → "Accommodation"

Return ONLY a valid JSON array. No explanations.
Example output:
[
  {{"description": "Factory electricity bill", "amount": 145000, "unit": "kWh", "region": "IN-KA", "activity_date": "2024-01-15", "year": 2024, "category": "Electricity", "supplier_name": null}}
]
"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mistral-large-latest",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                print(f"[PDF OCR] AI extraction API response status: success")
                choices = result.get("choices", [])
                if not choices:
                    print(f"[PDF OCR] AI extraction returned no choices")
                    return []
                
                content = choices[0].get("message", {}).get("content", "")
                print(f"[PDF OCR] AI extraction content length: {len(content)}")
                print(f"[PDF OCR] AI extraction content preview: {content[:500] if content else 'empty'}...")
                parsed = self._parse_json_response(content)
                print(f"[PDF OCR] Parsed JSON resulted in {len(parsed)} activities")
                return parsed
                
            except httpx.HTTPStatusError as e:
                print(f"[PDF OCR] AI extraction API HTTP error: {e.response.status_code} - {e.response.text[:500]}")
                logger.error(f"Activity extraction failed: HTTP {e.response.status_code}")
                return []
            except httpx.TimeoutException as e:
                print(f"[PDF OCR] AI extraction timed out: {str(e)}")
                logger.error(f"Activity extraction timed out")
                return []
            except Exception as e:
                print(f"[PDF OCR] AI extraction failed with exception: {type(e).__name__}: {str(e)}")
                print(f"[PDF OCR] Traceback: {traceback.format_exc()}")
                logger.error(f"Activity extraction failed: {type(e).__name__}: {str(e)}")
                return []
    
    def _parse_json_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse JSON response from AI, handling various formats"""
        try:
            # Clean markdown code blocks if present
            clean_content = content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content[7:]
            if clean_content.startswith("```"):
                clean_content = clean_content[3:]
            if clean_content.endswith("```"):
                clean_content = clean_content[:-3]
            clean_content = clean_content.strip()
            
            data = json.loads(clean_content)
            
            # Handle different response formats
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                # Check for common wrapper keys
                for key in ["activities", "data", "records", "rows"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                # If it's a single activity dict, wrap in list
                if "description" in data:
                    return [data]
            
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e} - Content: {content[:200]}...")
            return []
    
    def validate_activities(self, activities: List[Dict[str, Any]]) -> tuple[List[Dict], List[Dict]]:
        """
        Validate extracted activities against required fields.
        
        Args:
            activities: List of activity dictionaries
            
        Returns:
            Tuple of (valid_activities, invalid_activities)
        """
        valid = []
        invalid = []
        
        for idx, activity in enumerate(activities):
            missing_fields = []
            
            for field in self.REQUIRED_FIELDS:
                value = activity.get(field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    missing_fields.append(field)
            
            if missing_fields:
                invalid.append({
                    "index": idx,
                    "activity": activity,
                    "missing_fields": missing_fields
                })
            else:
                valid.append(activity)
        
        return valid, invalid
    
    def _parse_markdown_table(self, ocr_content: str) -> List[Dict[str, Any]]:
        """
        Parse markdown table directly from OCR output without using AI.
        Much faster and more reliable for tabular data.
        """
        print(f"[PDF OCR] Attempting direct markdown table parsing...")
        
        activities = []
        lines = ocr_content.strip().split('\n')
        
        # Find header row (line with column names)
        headers = []
        data_start_idx = 0
        
        for i, line in enumerate(lines):
            if '|' in line and 'Activity' in line or 'Description' in line:
                # Parse header columns
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if parts:
                    headers = parts
                    data_start_idx = i + 2  # Skip separator row
                    break
        
        if not headers:
            print(f"[PDF OCR] No table headers found in OCR content")
            return []
        
        print(f"[PDF OCR] Found headers: {headers}")
        
        # Map columns to standard field names
        column_mapping = {}
        for idx, col in enumerate(headers):
            col_lower = col.lower().strip()
            if 'description' in col_lower or 'activity' in col_lower:
                column_mapping['description'] = idx
            elif 'value' in col_lower or 'amount' in col_lower or 'consumption' in col_lower or 'quantity' in col_lower:
                column_mapping['amount'] = idx
            elif 'unit' in col_lower:
                column_mapping['unit'] = idx
            elif 'location' in col_lower or 'region' in col_lower or 'country' in col_lower:
                column_mapping['region'] = idx
            elif 'time' in col_lower or 'period' in col_lower or 'date' in col_lower or 'month' in col_lower:
                column_mapping['activity_date'] = idx
        
        print(f"[PDF OCR] Column mapping: {column_mapping}")
        
        # Parse data rows
        for line in lines[data_start_idx:]:
            if '|' not in line or '---' in line:
                continue
            
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) < 3:  # Need at least description, amount, unit
                continue
            
            try:
                activity = {}
                
                # Extract fields using column mapping
                if 'description' in column_mapping and column_mapping['description'] < len(parts):
                    activity['description'] = parts[column_mapping['description']]
                
                if 'amount' in column_mapping and column_mapping['amount'] < len(parts):
                    amount_str = parts[column_mapping['amount']].replace(',', '').strip()
                    try:
                        activity['amount'] = float(amount_str) if '.' in amount_str else int(amount_str)
                    except:
                        activity['amount'] = 0
                
                if 'unit' in column_mapping and column_mapping['unit'] < len(parts):
                    activity['unit'] = parts[column_mapping['unit']]
                
                if 'region' in column_mapping and column_mapping['region'] < len(parts):
                    region = parts[column_mapping['region']].strip()
                    # Normalize region to ISO alpha-2
                    region_map = {
                        'karnataka': 'IN', 'maharashtra': 'IN', 'delhi': 'IN', 'all india': 'IN',
                        'international': 'GLOBAL', 'global': 'GLOBAL',
                        'california': 'US', 'texas': 'US', 'new york': 'US',
                    }
                    activity['region'] = region_map.get(region.lower(), 'IN')
                
                if 'activity_date' in column_mapping and column_mapping['activity_date'] < len(parts):
                    date_str = parts[column_mapping['activity_date']]
                    # Parse dates like "January 2024", "Q1 2024", "Annual 2024"
                    activity['activity_date'], activity['year'] = self._parse_date_string(date_str)
                else:
                    activity['activity_date'] = datetime.now().strftime('%Y-%m-%d')
                    activity['year'] = datetime.now().year
                
                # Infer category from description
                activity['category'] = self._infer_category(activity.get('description', ''))
                
                # Add if we have the required fields
                if activity.get('description') and activity.get('amount'):
                    activities.append(activity)
                    
            except Exception as e:
                print(f"[PDF OCR] Error parsing row: {line[:50]}... - {str(e)}")
                continue
        
        print(f"[PDF OCR] Direct parsing extracted {len(activities)} activities")
        return activities
    
    def _parse_date_string(self, date_str: str) -> tuple:
        """Parse various date formats and return (activity_date, year)"""
        date_str = date_str.strip()
        
        # Try to extract year
        year_match = re.search(r'20\d{2}', date_str)
        year = int(year_match.group()) if year_match else datetime.now().year
        
        # Month mapping
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8,
            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Find month
        month = 1
        date_lower = date_str.lower()
        for month_name, month_num in months.items():
            if month_name in date_lower:
                month = month_num
                break
        
        # Handle quarterly/annual
        if 'q1' in date_lower:
            month = 2
        elif 'q2' in date_lower:
            month = 5
        elif 'q3' in date_lower:
            month = 8
        elif 'q4' in date_lower:
            month = 11
        elif 'annual' in date_lower:
            month = 7
        
        activity_date = f"{year}-{month:02d}-15"
        return activity_date, year
    
    def _infer_category(self, description: str) -> str:
        """Infer activity category from description"""
        desc_lower = description.lower()
        
        if any(kw in desc_lower for kw in ['electricity', 'power', 'kwh', 'compressed air']):
            return 'Electricity'
        elif any(kw in desc_lower for kw in ['diesel', 'fuel', 'lpg', 'gas', 'petrol', 'forklift']):
            return 'Fuel'
        elif any(kw in desc_lower for kw in ['flight', 'air travel', 'domestic', 'international']):
            return 'Business Travel'
        elif any(kw in desc_lower for kw in ['train', 'rail']):
            return 'Business Travel'
        elif any(kw in desc_lower for kw in ['taxi', 'cab', 'vehicle']):
            return 'Business Travel'
        elif any(kw in desc_lower for kw in ['freight', 'transport', 'courier', 'parcel']):
            return 'Freight'
        elif any(kw in desc_lower for kw in ['employee commute', 'commute', 'bus']):
            return 'Employee Commute'
        elif any(kw in desc_lower for kw in ['hotel', 'accommodation']):
            return 'Accommodation'
        elif any(kw in desc_lower for kw in ['water', 'consumption']):
            return 'Water'
        elif any(kw in desc_lower for kw in ['material', 'purchase', 'packaging', 'raw']):
            return 'Procurement'
        elif any(kw in desc_lower for kw in ['waste', 'disposal', 'effluent']):
            return 'Waste'
        elif any(kw in desc_lower for kw in ['refrigerant', 'fire', 'cylinder', 'welding', 'nitrogen']):
            return 'Industrial Processes'
        elif any(kw in desc_lower for kw in ['paper', 'office', 'printer', 'cartridge']):
            return 'Office Supplies'
        else:
            return 'Other'


# Singleton instance
mistral_ocr_service = MistralOCRService()

