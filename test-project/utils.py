import re
from models import User

def validate_email(email):
    """Validate email format"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def create_user(username, email):
    """Create and validate a new user"""
    if validate_email(email):
        user = User(username, email)
        if user.validate():
            return user
    return None

def format_price(price):
    """Format price with currency symbol"""
    return f"${price:.2f}"

def calculate_tax(price, tax_rate=0.1):
    """Calculate tax amount"""
    return price * tax_rate
