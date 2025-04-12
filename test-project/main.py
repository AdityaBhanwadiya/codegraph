from models import User, Product
from utils import create_user, format_price, calculate_tax
from database import export_db, import_db
from api import register_user, get_user_info, create_product, backup_database, APIError

def initialize_app():
    """Initialize the application"""
    print("Initializing application...")
    try:
        import_db("backup.json")
        print("Database loaded from backup")
    except:
        print("No backup found, starting with empty database")

def run_demo():
    """Run a demonstration of the application"""
    print("\n=== Running Demo ===\n")
    
    # Register users
    try:
        result = register_user("alice", "alice@example.com")
        print(f"User registration: {result['message']}")
        
        result = register_user("bob", "bob@example.com")
        print(f"User registration: {result['message']}")
    except APIError as e:
        print(f"API Error: {str(e)}")
    
    # Create products
    try:
        result = create_product("Laptop", 999.99)
        print(f"Product creation: {result['message']} - Price: {result['price']}")
        
        result = create_product("Smartphone", 499.99)
        print(f"Product creation: {result['message']} - Price: {result['price']}")
    except APIError as e:
        print(f"API Error: {str(e)}")
    
    # Get user info
    try:
        user_info = get_user_info("alice")
        print(f"User info: {user_info}")
    except APIError as e:
        print(f"API Error: {str(e)}")
    
    # Backup database
    try:
        result = backup_database("backup.json")
        print(f"Database backup: {result['message']}")
    except APIError as e:
        print(f"API Error: {str(e)}")

def main():
    """Main entry point"""
    initialize_app()
    run_demo()
    print("\nApplication completed successfully!")

if __name__ == "__main__":
    main()
