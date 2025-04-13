#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API module for the application.

This module provides API functions for user registration, product creation,
and other operations. It serves as the interface between the application's
core functionality and external clients.

Author: AI M.F.
Copyright (c) 2025 Example Corp.
License: MIT
"""

from typing import Dict, Any, Optional, Union
from models import User, Product
from utils import validate_email, format_price, calculate_tax
from database import get_user, get_product, export_db


class APIError(Exception):
    """
    Exception raised for API-related errors.
    
    This exception is used to signal errors that occur during API operations,
    such as validation failures or resource not found errors.
    
    Attributes:
        message (str): The error message
    """
    
    def __init__(self, message: str) -> None:
        """
        Initialize a new APIError instance.
        
        Args:
            message: The error message describing what went wrong
        """
        self.message = message
        super().__init__(self.message)


# User-related API functions
# --------------------------

def register_user(username: str, email: str) -> Dict[str, str]:
    """
    Register a new user in the system.
    
    This function validates the email format and user data, creates a new
    User instance, and saves it to the database.
    
    Args:
        username: The username for the new user
        email: The email address for the new user
        
    Returns:
        Dict[str, str]: A dictionary with status and message
        
    Raises:
        APIError: If the email format is invalid or user data validation fails
        
    Example:
        >>> try:
        ...     result = register_user("john_doe", "john@example.com")
        ...     print(result["message"])
        ... except APIError as e:
        ...     print(f"Error: {e}")
        User john_doe registered
    """
    # Validate email format
    if not validate_email(email):
        raise APIError("Invalid email format")
    
    # Create and validate user
    user = User(username, email)
    if not user.validate():
        raise APIError("Invalid user data")
    
    # Save user to database
    user.save()
    
    # Return success response
    return {
        "status": "success", 
        "message": f"User {username} registered"
    }


def get_user_info(username: str) -> Dict[str, Any]:
    """
    Get information about a user.
    
    Retrieves user data from the database based on the username.
    
    Args:
        username: The username of the user to retrieve
        
    Returns:
        Dict[str, Any]: The user data
        
    Raises:
        APIError: If the user is not found
        
    Example:
        >>> try:
        ...     user_data = get_user_info("john_doe")
        ...     print(f"Email: {user_data['email']}")
        ... except APIError as e:
        ...     print(f"Error: {e}")
        Email: john@example.com
    """
    # Get user data from database
    user_data = get_user(username)
    
    # Raise error if user not found
    if not user_data:
        raise APIError(f"User {username} not found")
    
    # Return user data
    return user_data


# Product-related API functions
# ----------------------------

def create_product(name: str, price: float) -> Dict[str, Any]:
    """
    Create a new product in the system.
    
    This function validates the product price, creates a new Product instance,
    and saves it to the database.
    
    Args:
        name: The name of the product
        price: The price of the product
        
    Returns:
        Dict[str, Any]: A dictionary with status, message, and price information
        
    Raises:
        APIError: If the price is not positive
        
    Example:
        >>> try:
        ...     result = create_product("Laptop", 999.99)
        ...     print(f"{result['message']} - {result['price']}")
        ... except APIError as e:
        ...     print(f"Error: {e}")
        Product Laptop created - $999.99
    """
    # Validate price
    if price <= 0:
        raise APIError("Price must be positive")
    
    # Create and save product
    product = Product(name, price)
    product.save()
    
    # Calculate price with tax
    tax_amount = calculate_tax(price)
    total_price = price + tax_amount
    
    # Return success response with price information
    return {
        "status": "success", 
        "message": f"Product {name} created",
        "price": format_price(price),
        "price_with_tax": format_price(total_price)
    }


# Database management API functions
# --------------------------------

def backup_database(filepath: str) -> Dict[str, str]:
    """
    Backup the database to a file.
    
    Exports the current state of the database to a JSON file at the
    specified path.
    
    Args:
        filepath: The path where the backup file will be saved
        
    Returns:
        Dict[str, str]: A dictionary with status and message
        
    Raises:
        APIError: If the backup operation fails
        
    Example:
        >>> try:
        ...     result = backup_database("backup.json")
        ...     print(result["message"])
        ... except APIError as e:
        ...     print(f"Error: {e}")
        Database backed up to backup.json
    """
    try:
        # Export database to file
        export_db(filepath)
        
        # Return success response
        return {
            "status": "success", 
            "message": f"Database backed up to {filepath}"
        }
    except Exception as e:
        # Raise APIError with details if export fails
        raise APIError(f"Backup failed: {str(e)}")
