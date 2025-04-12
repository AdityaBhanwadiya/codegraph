#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main application module.

This module serves as the entry point for the application. It initializes
the application, runs a demonstration of its features, and provides a
clean shutdown.

Author: Development Team
Copyright (c) 2025 Example Corp.
License: MIT
"""

from typing import Dict, Any, Optional
from models import User, Product
from utils import create_user, format_price, calculate_tax
from database import export_db, import_db
from api import register_user, get_user_info, create_product, backup_database, APIError


def initialize_app() -> None:
    """
    Initialize the application.
    
    This function sets up the application environment, including loading
    any existing database backup. If no backup is found, it starts with
    an empty database.
    
    Returns:
        None
    """
    print("Initializing application...")
    
    try:
        # Attempt to load the database from backup
        if import_db("backup.json"):
            print("Database loaded from backup")
        else:
            print("Failed to load backup, starting with empty database")
    except Exception as e:
        # Handle any exceptions during initialization
        print(f"No backup found, starting with empty database: {str(e)}")


def run_demo() -> None:
    """
    Run a demonstration of the application's features.
    
    This function demonstrates the core functionality of the application,
    including user registration, product creation, data retrieval, and
    database backup.
    
    Returns:
        None
    """
    print("\n=== Running Demo ===\n")
    
    # SECTION: User Registration
    # --------------------------
    print("--- User Registration ---")
    try:
        # Register first user
        result = register_user("alice", "alice@example.com")
        print(f"User registration: {result['message']}")
        
        # Register second user
        result = register_user("bob", "bob@example.com")
        print(f"User registration: {result['message']}")
    except APIError as e:
        # Handle API errors during user registration
        print(f"API Error: {str(e)}")
    
    # SECTION: Product Creation
    # ------------------------
    print("\n--- Product Creation ---")
    try:
        # Create first product
        result = create_product("Laptop", 999.99)
        print(f"Product creation: {result['message']} - Price: {result['price']}")
        
        # Create second product
        result = create_product("Smartphone", 499.99)
        print(f"Product creation: {result['message']} - Price: {result['price']}")
    except APIError as e:
        # Handle API errors during product creation
        print(f"API Error: {str(e)}")
    
    # SECTION: Data Retrieval
    # ----------------------
    print("\n--- Data Retrieval ---")
    try:
        # Retrieve user information
        user_info = get_user_info("alice")
        print(f"User info: {user_info}")
    except APIError as e:
        # Handle API errors during data retrieval
        print(f"API Error: {str(e)}")
    
    # SECTION: Database Backup
    # -----------------------
    print("\n--- Database Backup ---")
    try:
        # Backup the database
        result = backup_database("backup.json")
        print(f"Database backup: {result['message']}")
    except APIError as e:
        # Handle API errors during database backup
        print(f"API Error: {str(e)}")


def main() -> None:
    """
    Main entry point for the application.
    
    This function orchestrates the application flow by initializing
    the application, running the demonstration, and providing a clean
    shutdown.
    
    Returns:
        None
    """
    try:
        # Initialize the application
        initialize_app()
        
        # Run the demonstration
        run_demo()
        
        # Successful completion message
        print("\nApplication completed successfully!")
    except Exception as e:
        # Handle any unexpected exceptions
        print(f"\nApplication error: {str(e)}")
        return 1
    
    # Return success code
    return 0


# Execute main function if this script is run directly
if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
