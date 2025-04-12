#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database module for the application.

This module provides functions for storing, retrieving, and managing
data in a simulated in-memory database. It also includes functions for
importing and exporting the database to JSON files.

Author: Development Team
Copyright (c) 2025 Example Corp.
License: MIT
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, IO


# In-memory database structure
# This dictionary simulates a simple database with collections for users and products
_db: Dict[str, List[Dict[str, Any]]] = {
    'users': [],
    'products': []
}


def save_to_db(obj: Any) -> bool:
    """
    Save an object to the in-memory database.
    
    This function detects the object type based on its attributes and
    saves it to the appropriate collection in the database.
    
    Args:
        obj: The object to save (either User or Product)
        
    Returns:
        bool: True if the object was saved successfully, False otherwise
        
    Note:
        Objects are identified as users if they have a 'username' attribute,
        and as products if they have a 'price' attribute.
    """
    # Get the current timestamp for the record
    timestamp = datetime.now().isoformat()
    
    # Check if the object is a User (has username attribute)
    if hasattr(obj, 'username'):
        # Create a dictionary representation of the user
        user_data = {
            'username': obj.username,
            'email': obj.email,
            'created_at': timestamp
        }
        # Add to the users collection
        _db['users'].append(user_data)
        return True
    
    # Check if the object is a Product (has price attribute)
    elif hasattr(obj, 'price'):
        # Create a dictionary representation of the product
        product_data = {
            'name': obj.name,
            'price': obj.price,
            'created_at': timestamp
        }
        # Add to the products collection
        _db['products'].append(product_data)
        return True
    
    # Return False if the object type is not recognized
    return False


def get_user(username: str) -> Optional[Dict[str, Any]]:
    """
    Get a user by username.
    
    Searches the users collection for a user with the specified username.
    
    Args:
        username: The username to search for
        
    Returns:
        Optional[Dict[str, Any]]: The user data if found, None otherwise
        
    Example:
        >>> save_to_db(User("john_doe", "john@example.com"))
        True
        >>> user = get_user("john_doe")
        >>> user['username']
        'john_doe'
        >>> get_user("nonexistent_user") is None
        True
    """
    # Search for the user in the users collection
    for user in _db['users']:
        if user['username'] == username:
            return user
    
    # Return None if the user is not found
    return None


def get_product(name: str) -> Optional[Dict[str, Any]]:
    """
    Get a product by name.
    
    Searches the products collection for a product with the specified name.
    
    Args:
        name: The product name to search for
        
    Returns:
        Optional[Dict[str, Any]]: The product data if found, None otherwise
        
    Example:
        >>> save_to_db(Product("Laptop", 999.99))
        True
        >>> product = get_product("Laptop")
        >>> product['name']
        'Laptop'
        >>> get_product("Nonexistent Product") is None
        True
    """
    # Search for the product in the products collection
    for product in _db['products']:
        if product['name'] == name:
            return product
    
    # Return None if the product is not found
    return None


def export_db(filepath: str) -> None:
    """
    Export the database to a JSON file.
    
    Serializes the entire database to a JSON file at the specified path.
    
    Args:
        filepath: The path where the JSON file will be saved
        
    Raises:
        IOError: If the file cannot be written
        
    Example:
        >>> export_db("backup.json")  # Exports the database to backup.json
    """
    # Open the file in write mode
    with open(filepath, 'w') as f:
        # Serialize the database to JSON with pretty formatting
        json.dump(_db, f, indent=2)


def import_db(filepath: str) -> bool:
    """
    Import the database from a JSON file.
    
    Deserializes a JSON file and replaces the current database with its contents.
    
    Args:
        filepath: The path to the JSON file to import
        
    Returns:
        bool: True if the import was successful, False otherwise
        
    Example:
        >>> import_db("backup.json")  # Imports the database from backup.json
    """
    global _db
    
    # Check if the file exists
    if os.path.exists(filepath):
        try:
            # Open the file in read mode
            with open(filepath, 'r') as f:
                # Replace the current database with the contents of the file
                _db = json.load(f)
            return True
        except (json.JSONDecodeError, IOError):
            # Return False if there's an error reading or parsing the file
            return False
    
    # Return False if the file doesn't exist
    return False
