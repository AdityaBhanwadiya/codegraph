#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility functions for the application.

This module provides various utility functions for email validation,
user creation, price formatting, and tax calculation.

Author: AI M.F.
Copyright (c) 2025 Example Corp.
License: MIT
"""

import re
from typing import Optional, Union, Pattern
from models import User


def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Uses a regular expression to check if the provided string matches
    a basic email format. This is a simple validation and does not
    guarantee that the email actually exists.
    
    Args:
        email: The email address to validate
        
    Returns:
        bool: True if the email format is valid, False otherwise
        
    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    # Regular expression for basic email validation
    pattern: Pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def create_user(username: str, email: str) -> Optional[User]:
    """
    Create and validate a new user.
    
    This function creates a new User instance, validates the email format
    and the user data, and returns the user if valid.
    
    Args:
        username: The username for the new user
        email: The email address for the new user
        
    Returns:
        Optional[User]: A new User instance if validation passes, None otherwise
        
    Example:
        >>> user = create_user("john_doe", "john@example.com")
        >>> print(user.username if user else "Invalid user")
        john_doe
        >>> invalid_user = create_user("jane_doe", "invalid-email")
        >>> print(invalid_user)
        None
    """
    # First validate the email format
    if validate_email(email):
        # Create a new user instance
        user = User(username, email)
        # Validate the user data
        if user.validate():
            return user
    # Return None if validation fails
    return None


def format_price(price: float) -> str:
    """
    Format a price with a currency symbol.
    
    Converts a numeric price to a string with a dollar sign and
    two decimal places.
    
    Args:
        price: The price value to format
        
    Returns:
        str: The formatted price string
        
    Example:
        >>> format_price(10.5)
        '$10.50'
        >>> format_price(1000)
        '$1000.00'
    """
    # Format with dollar sign and two decimal places
    return f"${price:.2f}"


def calculate_tax(price: float, tax_rate: float = 0.1) -> float:
    """
    Calculate the tax amount for a given price.
    
    Multiplies the price by the tax rate to get the tax amount.
    
    Args:
        price: The price to calculate tax on
        tax_rate: The tax rate as a decimal (default: 0.1 or 10%)
        
    Returns:
        float: The calculated tax amount
        
    Example:
        >>> calculate_tax(100)  # Default 10% tax rate
        10.0
        >>> calculate_tax(100, 0.05)  # 5% tax rate
        5.0
    """
    # Calculate tax amount based on price and rate
    return price * tax_rate
