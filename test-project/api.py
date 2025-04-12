from models import User, Product
from utils import validate_email, format_price, calculate_tax
from database import get_user, get_product, export_db

class APIError(Exception):
    """API Error Exception"""
    pass

def register_user(username, email):
    """Register a new user"""
    if not validate_email(email):
        raise APIError("Invalid email format")
    
    user = User(username, email)
    if not user.validate():
        raise APIError("Invalid user data")
    
    user.save()
    return {"status": "success", "message": f"User {username} registered"}

def get_user_info(username):
    """Get user information"""
    user_data = get_user(username)
    if not user_data:
        raise APIError(f"User {username} not found")
    return user_data

def create_product(name, price):
    """Create a new product"""
    if price <= 0:
        raise APIError("Price must be positive")
    
    product = Product(name, price)
    product.save()
    return {
        "status": "success", 
        "message": f"Product {name} created",
        "price": format_price(price),
        "price_with_tax": format_price(price + calculate_tax(price))
    }

def backup_database(filepath):
    """Backup the database to a file"""
    try:
        export_db(filepath)
        return {"status": "success", "message": f"Database backed up to {filepath}"}
    except Exception as e:
        raise APIError(f"Backup failed: {str(e)}")
