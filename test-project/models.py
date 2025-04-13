#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Models module for the application.

This module defines the core data models used throughout the application,
including User and Product classes with their associated methods.

Author: AI M.F.
Copyright (c) 2025 Example Corp.
License: MIT
"""

from typing import Optional, Union, Dict, Any


class User:
    """
    User model representing application users.
    
    This class encapsulates user data and provides methods for validation
    and persistence. Each user has a unique username and an email address.
    
    Attributes:
        username (str): The user's unique identifier
        email (str): The user's email address
    """
    
    def __init__(self, username: str, email: str) -> None:
        """
        Initialize a new User instance.
        
        Args:
            username: A unique identifier for the user
            email: A valid email address for the user
        
        Example:
            >>> user = User("john_doe", "john@example.com")
        """
        self.username = username
        self.email = email
        
    def validate(self) -> bool:
        """
        Validate the user data.
        
        Ensures that the username is not empty and the email contains
        an '@' symbol as a basic validation check.
        
        Returns:
            bool: True if the user data is valid, False otherwise
            
        Example:
            >>> user = User("john_doe", "john@example.com")
            >>> user.validate()
            True
            >>> invalid_user = User("", "invalid-email")
            >>> invalid_user.validate()
            False
        """
        # Check for non-empty username and proper email format
        return len(self.username) > 0 and '@' in self.email
        
    def save(self) -> bool:
        """
        Save the user to the database.
        
        This method persists the user data to the database using the
        save_to_db function from the database module.
        
        Returns:
            bool: True if the save operation was successful, False otherwise
            
        Note:
            This method imports the database module at runtime to avoid
            circular imports.
        """
        # Import at runtime to avoid circular imports
        from database import save_to_db
        return save_to_db(self)


class Product:
    """
    Product model representing items for sale.
    
    This class encapsulates product data and provides methods for price
    manipulation and persistence.
    
    Attributes:
        name (str): The product's name
        price (float): The product's price in USD
    """
    
    def __init__(self, name: str, price: float) -> None:
        """
        Initialize a new Product instance.
        
        Args:
            name: The name of the product
            price: The price of the product in USD
            
        Example:
            >>> product = Product("Laptop", 999.99)
        """
        self.name = name
        self.price = price
        
    def discount(self, percent: float) -> None:
        """
        Apply a discount to the product's price.
        
        Args:
            percent: The discount percentage (0-100)
            
        Example:
            >>> product = Product("Laptop", 1000.0)
            >>> product.discount(20)  # Apply 20% discount
            >>> product.price
            800.0
        """
        # Calculate the discounted price
        self.price = self.price * (1 - percent / 100)
        
    def save(self) -> bool:
        """
        Save the product to the database.
        
        This method persists the product data to the database using the
        save_to_db function from the database module.
        
        Returns:
            bool: True if the save operation was successful, False otherwise
            
        Note:
            This method imports the database module at runtime to avoid
            circular imports.
        """
        # Import at runtime to avoid circular imports
        from database import save_to_db
        return save_to_db(self)
