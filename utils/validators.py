"""
Validation utilities for form data
"""
import re
from datetime import datetime

def validate_card_number(card_number: str) -> tuple[bool, str]:
    """
    Validate credit card number using Luhn algorithm
    
    Args:
        card_number: Card number string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Remove spaces and dashes
    card_number = re.sub(r'[\s-]', '', card_number)
    
    # Check if it's all digits
    if not card_number.isdigit():
        return False, "Card number must contain only digits"
    
    # Check length (13-19 digits for most cards)
    if len(card_number) < 13 or len(card_number) > 19:
        return False, "Card number must be between 13 and 19 digits"
    
    # Luhn algorithm
    def luhn_check(num):
        digits = [int(d) for d in num]
        checksum = 0
        
        # Double every second digit from right to left
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        
        checksum = sum(digits)
        return checksum % 10 == 0
    
    if not luhn_check(card_number):
        return False, "Invalid card number (failed Luhn check)"
    
    return True, ""

def validate_expiration_date(exp_date: str) -> tuple[bool, str]:
    """
    Validate expiration date (MM/YY or MM/YYYY format)
    
    Args:
        exp_date: Expiration date string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Try to parse MM/YY or MM/YYYY
    patterns = [
        (r'^(0[1-9]|1[0-2])/(\d{2})$', '%m/%y'),
        (r'^(0[1-9]|1[0-2])/(\d{4})$', '%m/%Y')
    ]
    
    for pattern, date_format in patterns:
        if re.match(pattern, exp_date):
            try:
                exp_datetime = datetime.strptime(exp_date, date_format)
                # To be valid, the card must not have expired. 
                # Cards expire at the END of the month.
                # So we check if the first day of the FOLLOWING month is in the past.
                if exp_datetime.month == 12:
                    next_month = exp_datetime.replace(year=exp_datetime.year + 1, month=1, day=1)
                else:
                    next_month = exp_datetime.replace(month=exp_datetime.month + 1, day=1)
                
                if next_month < datetime.now():
                    return False, "Card has expired"
                return True, ""
            except ValueError:
                continue
    
    return False, "Invalid expiration date format (use MM/YY or MM/YYYY)"

def validate_cvv(cvv: str, card_type: str = None) -> tuple[bool, str]:
    """
    Validate CVV/CVC code
    
    Args:
        cvv: CVV string
        card_type: Optional card type (Amex uses 4 digits, others use 3)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not cvv.isdigit():
        return False, "CVV must contain only digits"
    
    # American Express uses 4 digits, others use 3
    if card_type and 'amex' in card_type.lower():
        if len(cvv) != 4:
            return False, "CVV must be 4 digits for American Express"
    else:
        if len(cvv) != 3:
            return False, "CVV must be 3 digits"
    
    return True, ""

def validate_ssn(ssn: str) -> tuple[bool, str]:
    """
    Validate Social Security Number (9 digits)
    
    Args:
        ssn: SSN string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Remove dashes
    ssn_clean = re.sub(r'[-\s]', '', ssn)
    
    # Check if it's 9 digits
    if not ssn_clean.isdigit():
        return False, "SSN must contain only digits"
    
    if len(ssn_clean) != 9:
        return False, "SSN must be exactly 9 digits"
    
    # Check for invalid SSNs
    if ssn_clean == '000000000' or ssn_clean[0:3] == '000' or ssn_clean[3:5] == '00' or ssn_clean[5:9] == '0000':
        return False, "Invalid SSN format"
    
    return True, ""

def validate_name(name: str) -> tuple[bool, str]:
    """
    Validate name on card
    
    Args:
        name: Name string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 100:
        return False, "Name is too long"
    
    # Allow letters, spaces, hyphens, and apostrophes
    if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
        return False, "Name contains invalid characters"
    
    return True, ""

def sanitize_input(input_str: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks
    
    Args:
        input_str: Input string to sanitize
        
    Returns:
        Sanitized string
    """
    if not input_str:
        return ""
    
    # Remove any HTML tags
    sanitized = re.sub(r'<[^>]*>', '', input_str)
    
    # Remove any script tags or javascript
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    return sanitized
