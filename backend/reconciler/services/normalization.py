import re
from decimal import Decimal, InvalidOperation
from typing import Any

def normalize_reference(ref_string: Any) -> str:
    if ref_string is None:
        return ''
    raw = str(ref_string).strip()
    if not raw:
        return ''
    
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', raw).lower()
    if not cleaned:
        return ''
    
    if cleaned.isdigit():
        return f'rec{cleaned}'
    
    return cleaned


def safe_parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
    
    val_str = str(value).strip()
    if not val_str:
        return None
    
    if val_str.upper() in {'N/A', 'NULL', 'NONE', '-', 'NAN', 'UNDEFINED'}:
        return None
    
    cleaned = re.sub(r'[^\d.-]', '', val_str)
    if not cleaned or cleaned in {'.', '-', '-.'}:
        return None
    
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None
