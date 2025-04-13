import os
import time
import random
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI connection
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

class SummaryGenerator:
    """Generates concise summaries of code using Azure OpenAI."""
    
    def __init__(self):
        self.last_api_call = 0  # For rate limiting
        self.min_request_interval = 2.0  # Increased to 2 seconds between API calls
        self.max_retries = 5  # Maximum number of retries for rate-limited requests
        self.backoff_factor = 1.5  # Exponential backoff factor
    
    def generate_summary(self, code: str, max_words: int = 30) -> str:
        """
        Generate a concise summary of code using Azure OpenAI.
        
        Args:
            code: The function code to summarize
            max_words: Maximum number of words for the summary (default: 30)
            
        Returns:
            str: Concise summary of the code
        """
        return self._generate_azure_openai_summary(code, max_words)
    
    def _generate_azure_openai_summary(self, code: str, max_words: int = 30) -> str:
        """
        Generate a concise summary of code using Azure OpenAI.
        
        This method sends the code to Azure OpenAI and requests a concise summary
        that captures the essence of the function in the specified number of words.
        
        Args:
            code: The function code to summarize
            max_words: Maximum number of words for the summary (default: 30)
            
        Returns:
            str: Concise summary of the code
            
        Note:
            Requires Azure OpenAI API key and endpoint to be set in environment variables.
            Falls back to a simple extraction method if API call fails.
        """
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Check if Azure OpenAI credentials are available
        if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
            print("Warning: Azure OpenAI credentials not set. Using fallback summarization.")
            return self._fallback_summarization(code)
        
        # Prepare API request components
        api_url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": f"You are a code documentation assistant. Your task is to summarize Python functions into concise, informative summaries of {max_words} words or less. Focus on capturing the core functionality and purpose."
                },
                {
                    "role": "user",
                    "content": f"Summarize this Python function in {max_words} words or less:\n\n{code}"
                }
            ],
            "temperature": 0.3,
            "max_tokens": 100,
            "top_p": 1.0
        }
        
        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY
        }
        
        # Try with exponential backoff and retries
        retries = 0
        while retries <= self.max_retries:
            try:
                # Make the API call
                response = requests.post(api_url, headers=headers, json=payload)
                response.raise_for_status()  # Raise exception for HTTP errors
                
                # Parse the response
                result = response.json()
                summary = result["choices"][0]["message"]["content"].strip()
                
                return summary
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    retries += 1
                    if retries > self.max_retries:
                        print(f"Max retries exceeded. Using fallback summarization.")
                        return self._fallback_summarization(code)
                    
                    # Calculate backoff time with jitter
                    backoff_time = (self.backoff_factor ** retries) + (random.random() * 0.5)
                    print(f"Rate limited. Retrying in {backoff_time:.2f} seconds... (Attempt {retries}/{self.max_retries})")
                    time.sleep(backoff_time)
                else:
                    print(f"HTTP error calling Azure OpenAI API: {str(e)}")
                    return self._fallback_summarization(code)
            except Exception as e:
                print(f"Error calling Azure OpenAI API: {str(e)}")
                return self._fallback_summarization(code)
        
        # If we get here, all retries failed
        return self._fallback_summarization(code)
    
    def _fallback_summarization(self, code: str) -> str:
        """Generate a simple fallback summary when API calls fail."""
        # Extract function name and first line of docstring if available
        lines = code.split('\n')
        
        # Try to find function name
        function_name = ""
        for line in lines:
            if "def " in line:
                parts = line.split("def ")[1].split("(")[0].strip()
                function_name = parts
                break
        
        # Try to find docstring
        docstring = ""
        in_docstring = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                if not in_docstring and docstring:  # End of docstring
                    break
                continue
            if in_docstring:
                docstring += stripped + " "
        
        if docstring:
            # Return first sentence of docstring
            first_sentence = docstring.split('.')[0].strip()
            if len(first_sentence) > 100:
                return first_sentence[:97] + "..."
            return first_sentence
        
        if function_name:
            # Convert snake_case to words
            words = function_name.replace('_', ' ')
            return f"Function that appears to {words}"
        
        # Last resort
        if lines and len(lines) > 1:
            return lines[0].strip()[:100]
        return code[:100]
    
    def _apply_rate_limit(self):
        """Apply rate limiting to avoid too many API calls."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.min_request_interval:
            # Sleep to maintain the minimum interval between requests
            sleep_time = self.min_request_interval - time_since_last_call
            time.sleep(sleep_time)
        
        # Update the last API call time
        self.last_api_call = time.time()

# Example usage
if __name__ == "__main__":
    # Example code to summarize
    example_code = """
    def calculate_average(numbers):
        \"\"\"
        Calculate the average of a list of numbers.
        
        Args:
            numbers: List of numbers to average
            
        Returns:
            The average value
        \"\"\"
        if not numbers:
            return 0
        return sum(numbers) / len(numbers)
    """
    
    # Create a summary generator and generate a summary
    generator = SummaryGenerator()
    summary = generator.generate_summary(example_code)
    print(f"Summary: {summary}")
