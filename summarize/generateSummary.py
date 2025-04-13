import os
import time
import random
import asyncio
import aiohttp
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
        self.min_request_interval = 2.0  # Seconds between API calls
        self.max_retries = 5  # Maximum number of retries for rate-limited requests
        self.backoff_factor = 1.5  # Exponential backoff factor
        self.max_concurrent_requests = 3  # Maximum number of concurrent requests
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        self.lock = asyncio.Lock()  # For thread-safe rate limiting
    
    def generate_summary(self, code: str, max_words: int = 100) -> str:
        """
        Generate a concise summary of code using Azure OpenAI.
        
        Args:
            code: The function code to summarize
            max_words: Maximum number of words for the summary (default: 30)
            
        Returns:
            str: Concise summary of the code
        """
        # For backward compatibility, run the async method in a new event loop
        return asyncio.run(self.generate_summary_async(code, max_words))
    
    async def generate_summary_async(self, code: str, max_words: int = 30) -> str:
        """
        Asynchronously generate a concise summary of code using Azure OpenAI.
        
        Args:
            code: The function code to summarize
            max_words: Maximum number of words for the summary (default: 30)
            
        Returns:
            str: Concise summary of the code
        """
        return await self._generate_azure_openai_summary_async(code, max_words)
    
    async def _generate_azure_openai_summary_async(self, code: str, max_words: int = 30) -> str:
        """
        Asynchronously generate a concise summary of code using Azure OpenAI.
        
        This method sends the code to Azure OpenAI and requests a concise summary
        that captures the essence of the function in the specified number of words.
        
        Args:
            code: The function code to summarize
            max_words: Maximum number of words for the summary (default: 30)
            
        Returns:
            str: Concise summary of the code
        """
        # Check if Azure OpenAI credentials are available
        if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
            print("Warning: Azure OpenAI credentials not set. Using fallback summarization.")
            return self._fallback_summarization(code)
        
        # Prepare API request components
        api_url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
        
        system_prompt = (
            f"You are a code documentation assistant. Read the following function docstring "
            f"and generate a clear, concise, yet detailed summary. Your summary should explain:\n"
            f"- What the function does.\n"
            f"- The purpose of each parameter.\n"
            f"- What is returned by the function.\n"
            f"- Any exceptions that might be raised.\n"
            f"- A brief explanation of the provided usage example.\n"
            f"Just make sure your response is under {max_words} words."
        )
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Summarize this DocString in {max_words} words:\n\n{code}"
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
        
        # Use semaphore to limit concurrent requests
        async with self.semaphore:
            # Apply rate limiting
            await self._apply_rate_limit_async()
            
            # Try with exponential backoff and retries
            retries = 0
            while retries <= self.max_retries:
                try:
                    # Make the API call
                    async with aiohttp.ClientSession() as session:
                        async with session.post(api_url, headers=headers, json=payload) as response:
                            if response.status == 429:  # Too Many Requests
                                raise aiohttp.ClientResponseError(
                                    request_info=response.request_info,
                                    history=response.history,
                                    status=429,
                                    message="Too Many Requests",
                                    headers=response.headers
                                )
                            
                            response.raise_for_status()
                            result = await response.json()
                            summary = result["choices"][0]["message"]["content"].strip()
                            return summary
                
                except aiohttp.ClientResponseError as e:
                    if e.status == 429:  # Too Many Requests
                        retries += 1
                        if retries > self.max_retries:
                            print(f"Max retries exceeded. Using fallback summarization.")
                            return self._fallback_summarization(code)
                        
                        # Calculate backoff time with jitter
                        backoff_time = (self.backoff_factor ** retries) + (random.random() * 0.5)
                        print(f"Rate limited. Retrying in {backoff_time:.2f} seconds... (Attempt {retries}/{self.max_retries})")
                        await asyncio.sleep(backoff_time)
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
    
    async def _apply_rate_limit_async(self):
        """Apply rate limiting to avoid too many API calls (async version)."""
        async with self.lock:
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            
            if time_since_last_call < self.min_request_interval:
                # Sleep to maintain the minimum interval between requests
                sleep_time = self.min_request_interval - time_since_last_call
                await asyncio.sleep(sleep_time)
            
            # Update the last API call time
            self.last_api_call = time.time()
    
    async def generate_summaries_batch(self, code_list: List[str], max_words: int = 30) -> List[str]:
        """
        Generate summaries for multiple code snippets in parallel.
        
        Args:
            code_list: List of code snippets to summarize
            max_words: Maximum number of words for each summary
            
        Returns:
            List of summaries corresponding to the input code snippets
        """
        tasks = [self.generate_summary_async(code, max_words) for code in code_list]
        return await asyncio.gather(*tasks)

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
    
    # Example of batch processing
    print("\nBatch processing example:")
    
    # Multiple code snippets
    code_snippets = [
        """
        def add(a, b):
            \"\"\"Add two numbers and return the result.\"\"\"
            return a + b
        """,
        """
        def multiply(a, b):
            \"\"\"Multiply two numbers and return the result.\"\"\"
            return a * b
        """,
        """
        def divide(a, b):
            \"\"\"Divide a by b and return the result.\"\"\"
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b
        """
    ]
    
    # Run batch processing
    async def run_batch():
        summaries = await generator.generate_summaries_batch(code_snippets)
        for i, summary in enumerate(summaries):
            print(f"Summary {i+1}: {summary}")
    
    # Run the async function
    asyncio.run(run_batch())
