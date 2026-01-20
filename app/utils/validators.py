import re


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Validate phone number (basic validation)"""
    # Remove spaces and dashes
    phone = re.sub(r'[\s\-]', '', phone)
    # Check if it's a valid phone number (10-15 digits)
    return re.match(r'^\+?[0-9]{10,15}$', phone) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, 'Password must be at least 6 characters'
    return True, None


def validate_username(username):
    """Validate username format"""
    if len(username) < 3:
        return False, 'Username must be at least 3 characters'
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, 'Username can only contain letters, numbers, and underscores'
    return True, None
