import os
import sys
import ast

def extract_docstrings_from_file(filepath: str) -> dict:
    """
    Parse a Python file and extract docstrings from all functions.
    
    Args:
        filepath (str): The path to the Python file to parse.
        
    Returns:
        dict: A dictionary where keys are function names and values are docstrings.
    """
    docstrings = {}
    
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            source = file.read()
    except Exception as e:
        print(f"[ERROR] Could not read file {filepath}: {e}")
        return docstrings
    
    try:
        # Parse source code into an AST
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        print(f"[ERROR] Syntax error in file {filepath}: {e}")
        return docstrings
    
    # Traverse the AST
    for node in ast.walk(tree):
        # Check for function definitions (including async)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_name = node.name
            docstring = ast.get_docstring(node) or "No docstring available."
            docstrings[func_name] = docstring
    
    return docstrings


def extract_docstrings_from_directory(directory: str) -> dict:
    """
    Recursively walk through a directory, extracting function docstrings
    from all .py files.
    
    Args:
        directory (str): Path to the directory containing Python files.
    
    Returns:
        dict: A mapping of filename -> (dict of func_name -> docstring).
    """
    results = {}
    
    # Walk through all subdirectories and files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                docstrings = extract_docstrings_from_file(filepath)
                if docstrings:
                    results[filepath] = docstrings
                    
    return results

############ Debugging stuff #################

# if __name__ == "__main__":
#     if len(sys.argv) < 2:
#         print("Usage: python extract_docstrings.py <directory_path>")
#         sys.exit(1)
    
#     target_dir = sys.argv[1]
#     if not os.path.isdir(target_dir):
#         print(f"[ERROR] {target_dir} is not a valid directory.")
#         sys.exit(1)
    
#     all_docstrings = extract_docstrings_from_directory(target_dir)
    
#     # Print out the results
#     for filepath, func_dict in all_docstrings.items():
#         print(f"\n--- Docstrings in {filepath} ---")
#         for func_name, doc in func_dict.items():
#             print(f"Function: {func_name}")
#             print(f"Docstring: {doc}")
#             print("-" * 50)
