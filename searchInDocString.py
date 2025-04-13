def get_function_docstring(function_name: str, all_docstrings: dict) -> str:
    """
    Search through the all_docstrings dictionary for the specified function name
    and return its docstring. If found in multiple files, returns the first occurrence.
    
    Args:
        function_name (str): The name of the function to search for.
        all_docstrings (dict): Dictionary mapping file paths to dicts of function docstrings.
        
    Returns:
        str: The docstring for the function, or a not found message.
    """
    for filepath, func_dict in all_docstrings.items():
        if function_name in func_dict:
            # You might also want to return the filepath in a real scenario.
            return func_dict[function_name]
    return f"Function '{function_name}' not found."

# # Example usage:
# if __name__ == "__main__":
#     # Suppose all_docstrings is populated by your extract_docstrings_from_directory function
#     # For demonstration, let's define a sample dictionary:
#     all_docstrings = {
#         "test-project/api.py": {
#             "register_user": "Registers a new user with provided info.",
#             "login_user": "Handles the login process for users."
#         },
#         "test-project/utils.py": {
#             "calculate_tax": "Calculates tax based on price and tax rate."
#         }
#     }
    
#     # Now, search for a function name:
#     func_name = "calculate_tax"
#     docstring = get_function_docstring(func_name, all_docstrings)
#     print(f"Docstring for '{func_name}': {docstring}")
