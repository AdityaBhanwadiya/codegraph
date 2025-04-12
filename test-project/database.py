import json
import os
from datetime import datetime

# Simulate a database with a dictionary
_db = {
    'users': [],
    'products': []
}

def save_to_db(obj):
    """Save an object to the database"""
    if hasattr(obj, 'username'):
        _db['users'].append({
            'username': obj.username,
            'email': obj.email,
            'created_at': datetime.now().isoformat()
        })
        return True
    elif hasattr(obj, 'price'):
        _db['products'].append({
            'name': obj.name,
            'price': obj.price,
            'created_at': datetime.now().isoformat()
        })
        return True
    return False

def get_user(username):
    """Get a user by username"""
    for user in _db['users']:
        if user['username'] == username:
            return user
    return None

def get_product(name):
    """Get a product by name"""
    for product in _db['products']:
        if product['name'] == name:
            return product
    return None

def export_db(filepath):
    """Export the database to a JSON file"""
    with open(filepath, 'w') as f:
        json.dump(_db, f, indent=2)

def import_db(filepath):
    """Import the database from a JSON file"""
    global _db
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            _db = json.load(f)
