import csv
from io import StringIO, BytesIO
from typing import List, Dict, Tuple
from datetime import datetime

try:
    from openpyxl import load_workbook
except ImportError:  # pragma: no cover - optional XLSX support
    load_workbook = None

class CSVParsingService:
    """Service for parsing and validating CSV files"""
    
    REQUIRED_COLUMNS = {
        'description': str,
        'transaction_date': 'datetime',
        'scope': int,
        'category': str,
        'activity_value': float,
        'activity_unit': str,
        'emission_factor_value': float
    }
    
    OPTIONAL_COLUMNS = {
        'supplier_name': str,
        'project_id': str,
        'notes': str
    }
    
    VALID_SCOPES = [1, 2, 3]
    
    @staticmethod
    def parse_csv(file_content: bytes, encoding: str = 'utf-8') -> Tuple[List[Dict], List[Dict]]:
        """
        Parse CSV file with error handling
        
        Args:
            file_content: Byte content of CSV file
            encoding: File encoding (default: utf-8)
            
        Returns:
            (valid_rows, error_rows)
            
        Raises:
            Tuple containing:
            - valid_rows: List of valid row dictionaries
            - error_rows: List of error dictionaries with row number and error message
        """
        
        # Try to decode with specified encoding, fallback to iso-8859-1
        try:
            text = file_content.decode(encoding)
        except UnicodeDecodeError:
            try:
                text = file_content.decode('iso-8859-1')
            except Exception:
                return [], [{"row": 0, "error": "Cannot decode file (unsupported encoding)"}]
        
        # Handle different line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        try:
            csv_reader = csv.DictReader(StringIO(text))
        except Exception as e:
            return [], [{"row": 0, "error": f"Invalid CSV format: {str(e)}"}]
        
        if not csv_reader.fieldnames:
            return [], [{"row": 0, "error": "Empty CSV file or no header row"}]
        
        valid_rows = []
        error_rows = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header=1)
            # Skip empty rows
            if all(not cell.strip() if isinstance(cell, str) else not cell for cell in row.values()):
                continue
            
            is_valid, error_msg = CSVParsingService.validate_row(row, row_num)
            
            if is_valid:
                # Add row number for tracking
                row["_row_num"] = row_num
                valid_rows.append(row)
            else:
                error_rows.append({"row": row_num, "error": error_msg})
        
        return valid_rows, error_rows
    
    @staticmethod
    def parse_xlsx(file_content: bytes) -> Tuple[List[Dict], List[Dict]]:
        """
        Parse XLSX file with error handling.
        Falls back with a clear error if openpyxl is not installed.
        """
        if load_workbook is None:
            return [], [{"row": 0, "error": "XLSX parsing not available (missing openpyxl dependency)"}]

        try:
            wb = load_workbook(filename=BytesIO(file_content), read_only=True, data_only=True)
            sheet = wb.active
        except Exception as e:
            return [], [{"row": 0, "error": f"Invalid XLSX file: {str(e)}"}]

        rows_iter = sheet.iter_rows(values_only=True)
        try:
            headers = next(rows_iter)
        except StopIteration:
            return [], [{"row": 0, "error": "Empty XLSX file"}]

        headers = [str(h).strip() if h is not None else "" for h in headers]
        header_index = {h: idx for idx, h in enumerate(headers)}

        valid_rows: List[Dict] = []
        error_rows: List[Dict] = []

        row_num = 1  # header row
        for excel_row in rows_iter:
            row_num += 1
            row_dict: Dict[str, str] = {}

            for col_name in list(CSVParsingService.REQUIRED_COLUMNS.keys()) + list(CSVParsingService.OPTIONAL_COLUMNS.keys()):
                if col_name in header_index:
                    val = excel_row[header_index[col_name]]
                    row_dict[col_name] = "" if val is None else str(val)

            # Skip completely empty rows
            if all(not v.strip() for v in row_dict.values()):
                continue

            is_valid, error_msg = CSVParsingService.validate_row(row_dict, row_num)
            if is_valid:
                row_dict["_row_num"] = row_num
                valid_rows.append(row_dict)
            else:
                error_rows.append({"row": row_num, "error": error_msg})

        return valid_rows, error_rows

    @staticmethod
    def validate_row(row: Dict, row_num: int) -> Tuple[bool, str]:
        """
        Validate single row
        
        Args:
            row: Dictionary representing a CSV row
            row_num: Row number (for error reporting)
            
        Returns:
            (is_valid, error_message)
        """
        
        # Check for missing required fields
        for col in CSVParsingService.REQUIRED_COLUMNS.keys():
            if col not in row:
                return False, f"Missing column: {col}"
            
            if not row[col] or (isinstance(row[col], str) and not row[col].strip()):
                return False, f"Missing required field: {col}"
        
        # Validate description
        if len(row['description'].strip()) > 500:
            return False, "Description exceeds 500 characters"
        
        # Validate scope (1-3)
        try:
            scope = int(row['scope'].strip())
            if scope not in CSVParsingService.VALID_SCOPES:
                return False, f"Scope must be 1, 2, or 3. Got: {scope}"
        except ValueError:
            return False, f"Scope must be integer. Got: {row['scope']}"
        
        # Validate category
        if len(row['category'].strip()) > 100:
            return False, "Category exceeds 100 characters"
        
        # Validate activity_value (positive float)
        try:
            activity_val = float(row['activity_value'].strip())
            if activity_val <= 0:
                return False, f"Activity value must be positive. Got: {activity_val}"
        except ValueError:
            return False, f"Activity value must be number. Got: {row['activity_value']}"
        
        # Validate activity_unit
        if len(row['activity_unit'].strip()) > 50:
            return False, "Activity unit exceeds 50 characters"
        
        # Validate emission_factor_value (positive float)
        try:
            factor_val = float(row['emission_factor_value'].strip())
            if factor_val <= 0:
                return False, f"Emission factor must be positive. Got: {factor_val}"
        except ValueError:
            return False, f"Emission factor must be number. Got: {row['emission_factor_value']}"
        
        # Validate transaction_date
        try:
            date_str = row['transaction_date'].strip()
            # Try ISO format first
            if 'T' in date_str or ' ' in date_str:
                datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Try date-only format
                datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, KeyError):
            return False, f"Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Got: {row['transaction_date']}"

        # Optional fields length validation
        supplier = row.get('supplier_name') or ""
        if supplier and len(supplier.strip()) > 255:
            return False, "Supplier name exceeds 255 characters"

        project_id = row.get('project_id') or ""
        if project_id and len(project_id.strip()) > 100:
            return False, "Project ID exceeds 100 characters"

        notes = row.get('notes') or ""
        if notes and len(notes.strip()) > 1000:
            return False, "Notes field exceeds 1000 characters"

        # Basic spreadsheet formula injection guard on key text fields
        for field_name in ["description", "category", "supplier_name", "project_id", "notes"]:
            val = (row.get(field_name) or "").lstrip()
            if val and val[0] in ("=", "+", "-", "@"):
                return False, f"Potential formula injection detected in field '{field_name}'"

        return True, ""
    
    @staticmethod
    def calculate_co2e(activity_value: float, emission_factor: float) -> Tuple[float, float]:
        """
        Calculate CO2e emissions
        
        Formula: CO2e = activity_value × emission_factor
        
        Args:
            activity_value: Quantity of activity
            emission_factor: CO2e per unit of activity
            
        Returns:
            (co2e_kg, co2e_tonnes)
        """
        co2e_kg = activity_value * emission_factor
        co2e_tonnes = co2e_kg / 1000
        
        return round(co2e_kg, 3), round(co2e_tonnes, 6)