import os
import time
import random
import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI connection
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

class SearchExplainer:
    """Generates human-friendly explanations of search results using Azure OpenAI."""
    
    def __init__(self):
        self.last_api_call = 0  # For rate limiting
        self.min_request_interval = 2.0  # Seconds between API calls
        self.max_retries = 5  # Maximum number of retries for rate-limited requests
        self.backoff_factor = 1.5  # Exponential backoff factor
        self.lock = asyncio.Lock()  # For thread-safe rate limiting
    
    def explain_search_results(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        Generate a human-friendly explanation of search results using Azure OpenAI.
        
        Args:
            query: The original search query
            search_results: List of search results from Qdrant
            
        Returns:
            str: Human-friendly explanation of the search results
        """
        # For backward compatibility, run the async method in a new event loop
        return asyncio.run(self.explain_search_results_async(query, search_results))
    
    async def explain_search_results_async(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        Asynchronously generate a human-friendly explanation of search results using Azure OpenAI.
        
        Args:
            query: The original search query
            search_results: List of search results from Qdrant
            
        Returns:
            str: Human-friendly explanation of the search results
        """
        # Check if Azure OpenAI credentials are available
        if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
            print("Warning: Azure OpenAI credentials not set. Using fallback explanation.")
            return self._fallback_explanation(query, search_results)
        
        # Prepare API request components
        api_url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
        
        # Sort search results by score (highest first)
        sorted_results = sorted(search_results, key=lambda x: x['score'], reverse=True)
        
        # Format search results for the prompt
        formatted_results = self._format_search_results(sorted_results)
        
        system_prompt = (
            "You are a helpful coding assistant that explains search results from a codebase in a human-friendly way. "
            "Your goal is to help users understand the code they're looking for by providing clear explanations, examples, "
            "and relevant context. Your responses should be informative, educational, and accessible to developers of all levels."
            "\n\n"
            "When explaining search results:"
            "\n"
            "1. Create a COHESIVE, FLOWING explanation that starts with the most relevant result (highest similarity score) "
            "   and naturally transitions to other results in descending order of relevance\n"
            "2. Explain the purpose and functionality of the code in simple terms\n"
            "3. Show how the different results are connected to each other (e.g., function calls, imports, etc.)\n"
            "4. Provide practical examples of how the code might be used\n"
            "5. Include relevant links to documentation or tutorials when appropriate\n"
            "6. Format your response with clear headings, bullet points, and code blocks for readability\n"
            "7. If appropriate, suggest related concepts the user might want to explore\n"
            "\n"
            "Your explanation should feel like ONE COHESIVE ANSWER, not separate explanations for each result. "
            "Make your explanations educational and helpful, as if you're teaching someone about the code."
        )
        
        user_prompt = (
            f"I searched for: \"{query}\"\n\n"
            f"Here are the search results in order of relevance (highest similarity score first):\n\n{formatted_results}\n\n"
            f"Please explain these results in a human-friendly way as ONE COHESIVE FLOWING NARRATIVE. "
            f"Start with the most relevant result and naturally transition to other results. "
            f"Include explanations of what the code does, how it might be used, and any relevant concepts I should understand. "
            f"If possible, provide examples, links to documentation, or tutorials that might help me understand better. "
            f"Make sure your explanation feels like a single, unified answer, not separate explanations for each result."
        )
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.5,
            "max_tokens": 1000,
            "top_p": 1.0
        }
        
        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_OPENAI_API_KEY
        }
        
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
                        explanation = result["choices"][0]["message"]["content"].strip()
                        return explanation
            
            except aiohttp.ClientResponseError as e:
                if e.status == 429:  # Too Many Requests
                    retries += 1
                    if retries > self.max_retries:
                        print(f"Max retries exceeded. Using fallback explanation.")
                        return self._fallback_explanation(query, search_results)
                    
                    # Calculate backoff time with jitter
                    backoff_time = (self.backoff_factor ** retries) + (random.random() * 0.5)
                    print(f"Rate limited. Retrying in {backoff_time:.2f} seconds... (Attempt {retries}/{self.max_retries})")
                    await asyncio.sleep(backoff_time)
                else:
                    print(f"HTTP error calling Azure OpenAI API: {str(e)}")
                    return self._fallback_explanation(query, search_results)
            except Exception as e:
                print(f"Error calling Azure OpenAI API: {str(e)}")
                return self._fallback_explanation(query, search_results)
        
        # If we get here, all retries failed
        return self._fallback_explanation(query, search_results)
    
    def _format_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """Format search results for the prompt."""
        formatted = ""
        
        for i, result in enumerate(search_results):
            formatted += f"Result {i+1} (Relevance Score: {result['score']:.4f}):\n"
            
            # Check if this is a node or edge result
            metadata = result['metadata']
            if 'type' in metadata:  # Node
                formatted += f"Type: Node\n"
                formatted += f"Name: {metadata['name']}\n"
                formatted += f"Node Type: {metadata['type']}\n"
                
                if 'docstring_data' in metadata:
                    docstring = metadata['docstring_data']
                    formatted += f"Summary: {docstring.get('summary', '')}\n"
                    
                    if docstring.get('parameters'):
                        formatted += "Parameters:\n"
                        for param_name, param_desc in docstring['parameters'].items():
                            formatted += f"  - {param_name}: {param_desc}\n"
                    
                    if docstring.get('returns'):
                        formatted += f"Returns: {docstring.get('returns')}\n"
                    
                    if docstring.get('raises'):
                        formatted += f"Raises: {docstring.get('raises')}\n"
                    
                    if docstring.get('note'):
                        formatted += f"Note: {docstring.get('note')}\n"
                    
                    if docstring.get('example'):
                        formatted += f"Example: {docstring.get('example')}\n"
            else:  # Edge
                formatted += f"Type: Edge\n"
                formatted += f"Source: {metadata.get('source', '')}\n"
                formatted += f"Target: {metadata.get('target', '')}\n"
                formatted += f"Relation: {metadata.get('relation', '')}\n"
            
            formatted += "\n"
        
        return formatted
    
    def _fallback_explanation(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """Generate a simple fallback explanation when API calls fail."""
        explanation = f"Search results for: {query}\n\n"
        
        for i, result in enumerate(search_results):
            explanation += f"Result {i+1} (Relevance Score: {result['score']:.4f}):\n"
            
            # Check if this is a node or edge result
            metadata = result['metadata']
            if 'type' in metadata:  # Node
                explanation += f"- Found a {metadata['type']} named '{metadata['name']}'\n"
                
                if 'docstring_data' in metadata:
                    docstring = metadata['docstring_data']
                    explanation += f"  Summary: {docstring.get('summary', '')}\n"
            else:  # Edge
                explanation += f"- Found a relationship: {metadata.get('source', '')} -> {metadata.get('target', '')} ({metadata.get('relation', '')})\n"
        
        explanation += "\nFor more detailed explanations, please ensure Azure OpenAI credentials are properly configured."
        return explanation
    
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

# Example usage
if __name__ == "__main__":
    # Example search results
    example_results = [
        {
            "id": "some_id_1",
            "score": 0.95,
            "metadata": {
                "name": "validate_email",
                "type": "function",
                "docstring_data": {
                    "summary": "Validates an email address format.",
                    "parameters": {
                        "email": "The email address to validate"
                    },
                    "returns": "True if the email is valid, False otherwise",
                    "raises": "ValueError if the email is None",
                    "note": "",
                    "example": "validate_email('user@example.com') # Returns True"
                }
            }
        },
        {
            "id": "some_id_2",
            "score": 0.85,
            "metadata": {
                "source": "create_user",
                "target": "validate_email",
                "relation": "calls"
            }
        }
    ]
    
    # Create an explainer and generate an explanation
    explainer = SearchExplainer()
    explanation = explainer.explain_search_results("email validation", example_results)
    print(explanation)
