"""Validators"""
import re


def validate_password(password):
    """
    Validate password
    Requirements:
    - At least 8 characters
    - At least 1 special character
    - At least 1 digit
    """
    if len(password) < 8:
        return False, 'Password must be at least 8 characters'
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, 'Password must contain at least 1 special character'
    
    if not re.search(r'\d', password):
        return False, 'Password must contain at least 1 digit'
    
    return True, 'Password is valid'


def validate_email(email):
    """Validate email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_cccd(cccd):
    """Validate Vietnamese CCCD (ID number)"""
    # CCCD should be 12 digits
    return re.match(r'^\d{12}$', cccd) is not None


def validate_phone(phone):
    """Validate Vietnamese phone number"""
    return re.match(r'^(\+84|0)[1-9]\d{8}$', phone) is not None


def validate_date_format(date_str, format='%Y-%m-%d'):
    """Validate date format"""
    from datetime import datetime
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False
