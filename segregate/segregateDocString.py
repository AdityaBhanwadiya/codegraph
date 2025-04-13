import re


def parse_docstring(docstring: str) -> dict:
    """
    Parse a given docstring into structured components.
    
    Args:
        docstring (str): The full docstring of a function.
        
    Returns:
        dict: A dictionary with keys: 'summary', 'parameters', 'returns', 'raises', 'example'
    """
    # Remove leading and trailing whitespace
    docstring = docstring.strip()
    
    # Pattern to split sections based on keywords (non-capturing group)
    sections = re.split(r'\n(?=\w+?:)', docstring)
    
    # Initialize default structured data
    result = {
        'summary': '',
        'parameters': {},
        'returns': '',
        'raises': '',
        'note': '',
        'example': ''
    }
    
    # The first section is usually the summary part
    result['summary'] = sections[0].strip()
    
    # Process each subsequent section
    for section in sections[1:]:
        if section.startswith("Args:"):
            # Extract parameters, one per line
            params = re.findall(r'(\w+):\s*(.+)', section, re.DOTALL)
            for key, value in params:
                result['parameters'][key.strip()] = value.strip()
        elif section.startswith("Returns:"):
            result['returns'] = section.replace("Returns:", "").strip()
        elif section.startswith("Raises:"):
            result['raises'] = section.replace("Raises:", "").strip()
        elif section.startswith("Note:"):
            result['note'] = section.replace("Note:", "").strip()
        elif section.startswith("Example:"):
            result['example'] = section.replace("Example:", "").strip()
    
    return result

# # Example usage:
# doc = """
# Get information about a user.

# Retrieves user data from the database based on the username.

# Args:
#     username: The username of the user to retrieve
        
# Returns:
#     Dict[str, Any]: The user data
    
# Note:
#     jkaknjknfjkadkjfanfjasnfkasfnakj
        
# Example:
#     >>> try:
#     ...     user_data = get_user_info("john_doe")
#     ...     print(f"Email: {user_data['email']}")
#     ... except APIError as e:
#     ...     print(f"Error: {e}")
#     Email: john@example.com
# """

# parsed = parse_docstring(doc)
# print(parsed)
