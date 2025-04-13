import re
import string
from typing import Dict, Any, List, Union

def preprocess_text(text: str) -> str:
    """
    Preprocess text to improve similarity matching.
    
    This function:
    1. Removes extra whitespace and newlines
    2. Converts text to lowercase
    3. Removes unnecessary punctuation
    
    Args:
        text (str): The text to preprocess
        
    Returns:
        str: The preprocessed text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace multiple whitespace (including newlines) with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove punctuation except for those that might be meaningful in code contexts
    # Keep: @ (decorators, emails), _ (snake_case), . (method calls), # (comments), : (type hints)
    meaningful_chars = '@_.:# '
    punctuation_to_remove = ''.join(c for c in string.punctuation if c not in meaningful_chars)
    text = text.translate(str.maketrans('', '', punctuation_to_remove))
    
    # Remove extra spaces that might have been created
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text

def preprocess_docstring_data(docstring_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess all text fields in a docstring data dictionary.
    
    Args:
        docstring_data (Dict[str, Any]): The docstring data to preprocess
        
    Returns:
        Dict[str, Any]: The preprocessed docstring data
    """
    if not docstring_data:
        return {}
    
    # Create a copy to avoid modifying the original
    processed = {}
    
    # Process summary
    if 'summary' in docstring_data:
        processed['summary'] = preprocess_text(docstring_data['summary'])
    
    # Process parameters
    if 'parameters' in docstring_data and docstring_data['parameters']:
        processed['parameters'] = {}
        for param_name, param_desc in docstring_data['parameters'].items():
            processed['parameters'][param_name] = preprocess_text(param_desc)
    else:
        processed['parameters'] = {}
    
    # Process returns
    if 'returns' in docstring_data:
        processed['returns'] = preprocess_text(docstring_data['returns'])
    else:
        processed['returns'] = ""
    
    # Process raises
    if 'raises' in docstring_data:
        processed['raises'] = preprocess_text(docstring_data['raises'])
    else:
        processed['raises'] = ""
    
    # Process note
    if 'note' in docstring_data:
        processed['note'] = preprocess_text(docstring_data['note'])
    else:
        processed['note'] = ""
    
    # Process example
    if 'example' in docstring_data:
        processed['example'] = preprocess_text(docstring_data['example'])
    else:
        processed['example'] = ""
    
    return processed

def get_combined_text_for_embedding(docstring_data: Dict[str, Any]) -> str:
    """
    Combine all preprocessed text fields into a single string for embedding.
    
    Args:
        docstring_data (Dict[str, Any]): The preprocessed docstring data
        
    Returns:
        str: A combined text string for embedding
    """
    if not docstring_data:
        return ""
    
    parts = []
    
    # Add summary
    if docstring_data.get('summary'):
        parts.append(f"summary: {docstring_data['summary']}")
    
    # Add parameters
    if docstring_data.get('parameters'):
        param_texts = [f"{name}: {desc}" for name, desc in docstring_data['parameters'].items()]
        if param_texts:
            parts.append(f"parameters: {' '.join(param_texts)}")
    
    # Add returns
    if docstring_data.get('returns'):
        parts.append(f"returns: {docstring_data['returns']}")
    
    # Add raises
    if docstring_data.get('raises'):
        parts.append(f"raises: {docstring_data['raises']}")
    
    # Add note
    if docstring_data.get('note'):
        parts.append(f"note: {docstring_data['note']}")
    
    # Add example
    if docstring_data.get('example'):
        parts.append(f"example: {docstring_data['example']}")
    
    return " ".join(parts)

# Example usage
if __name__ == "__main__":
    # Example docstring data
    docstring_data = {
        "summary": "Validates an email address format.",
        "parameters": {
            "email": "The email address to validate"
        },
        "returns": "True if the email is valid, False otherwise",
        "raises": "ValueError if the email is None",
        "note": "",
        "example": "validate_email('user@example.com') # Returns True"
    }
    
    # Preprocess the docstring data
    processed_data = preprocess_docstring_data(docstring_data)
    print("Preprocessed docstring data:")
    for key, value in processed_data.items():
        print(f"{key}: {value}")
    
    # Get combined text for embedding
    combined_text = get_combined_text_for_embedding(processed_data)
    print("\nCombined text for embedding:")
    print(combined_text)
