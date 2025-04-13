# import os
# import time
# import json
# import uuid
# import requests
# import ast
# from typing import Dict, List, Any, Optional
# from datetime import datetime
# from dotenv import load_dotenv
# from pymongo import MongoClient
# import networkx as nx

# # Load environment variables
# load_dotenv()

# # MongoDB connection
# MONGO_URI = os.getenv("MONGO_URI")
# MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "code_summaries")
# MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "functions")

# # Azure OpenAI connection
# AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
# AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
# AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
# AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

# class DatabaseManager:
#     """Manages function summaries in MongoDB using Azure OpenAI."""
    
#     def __init__(self):
#         self.mongo_client = None
#         self.mongo_db = None
#         self.mongo_collection = None
#         self.last_api_call = 0  # For rate limiting
#         self.min_request_interval = 0.5  # Minimum seconds between API calls
        
#         # Initialize MongoDB connection
#         self._init_mongo()
    
#     def _init_mongo(self):
#         """Initialize MongoDB connection."""
#         try:
#             self.mongo_client = MongoClient(MONGO_URI)
#             self.mongo_db = self.mongo_client[MONGO_DB_NAME]
#             self.mongo_collection = self.mongo_db[MONGO_COLLECTION]
            
#             # Create text index for searching
#             self.mongo_collection.create_index([("summary", "text")])
#             print(f"Connected to MongoDB: {MONGO_DB_NAME}.{MONGO_COLLECTION}")
#         except Exception as e:
#             print(f"Error connecting to MongoDB: {str(e)}")
#             raise
    
#     def process_python_file(self, file_path: str) -> List[Dict]:
#         """
#         Extract functions from a Python file and generate summaries.
        
#         Args:
#             file_path: Path to the Python file
            
#         Returns:
#             List of function summaries
#         """
#         try:
#             # Read the file
#             with open(file_path, 'r', encoding='utf-8') as f:
#                 code = f.read()
            
#             # Parse the AST
#             tree = ast.parse(code)
            
#             # Extract functions and their docstrings
#             functions = []
#             for node in ast.walk(tree):
#                 if isinstance(node, ast.FunctionDef):
#                     # Get function code
#                     func_code = ast.get_source_segment(code, node)
                    
#                     # Get docstring
#                     docstring = ast.get_docstring(node) or ""
                    
#                     # Generate summary using Azure OpenAI
#                     summary = self._generate_azure_openai_summary(func_code)
                    
#                     # Store in MongoDB
#                     function_data = {
#                         "file_path": file_path,
#                         "function_name": node.name,
#                         "docstring": docstring,
#                         "summary": summary,
#                         "timestamp": self._get_timestamp()
#                     }
                    
#                     # Insert into MongoDB
#                     self.mongo_collection.update_one(
#                         {"file_path": file_path, "function_name": node.name},
#                         {"$set": function_data},
#                         upsert=True
#                     )
                    
#                     functions.append(function_data)
            
#             return functions
#         except Exception as e:
#             print(f"Error processing file {file_path}: {str(e)}")
#             return []
    
#     def store_graph(self, graph: nx.DiGraph, project_name: str) -> str:
#         """
#         Store graph data in MongoDB.
        
#         Args:
#             graph: NetworkX graph object containing code relationships
#             project_name: Name of the project for identification
            
#         Returns:
#             graph_id: Unique ID for the stored graph
#         """
#         # Generate a unique ID for this graph
#         graph_id = str(uuid.uuid4())
        
#         # Create basic metadata
#         metadata = {
#             "graph_id": graph_id,
#             "project_name": project_name,
#             "node_count": len(graph.nodes),
#             "edge_count": len(graph.edges),
#             "timestamp": self._get_timestamp()
#         }
        
#         # Store metadata in MongoDB
#         self.mongo_collection.insert_one(metadata)
#         print(f"Stored graph metadata in MongoDB with ID: {graph_id}")
        
#         return graph_id
    
#     def search_functions(self, query: str, limit: int = 10) -> List[Dict]:
#         """
#         Search for functions by summary or content.
        
#         Args:
#             query: The search query text
#             limit: Maximum number of results to return
            
#         Returns:
#             List of matching function summaries
#         """
#         try:
#             # Use MongoDB text search
#             results = self.mongo_collection.find(
#                 {"$text": {"$search": query}},
#                 {"score": {"$meta": "textScore"}}
#             ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
#             return list(results)
#         except Exception as e:
#             print(f"Error searching functions: {str(e)}")
#             return []
    
#     def list_graphs(self) -> List[Dict]:
#         """
#         List all stored graphs with basic metadata.
        
#         Returns:
#             List of graph metadata dictionaries
#         """
#         return list(self.mongo_collection.find(
#             {"graph_id": {"$exists": True}},
#             {
#                 "_id": 0,
#                 "graph_id": 1,
#                 "project_name": 1,
#                 "node_count": 1,
#                 "edge_count": 1,
#                 "timestamp": 1
#             }
#         ))
    
#     def delete_graph(self, graph_id: str) -> bool:
#         """
#         Delete a graph from MongoDB.
        
#         Args:
#             graph_id: ID of the graph to delete
            
#         Returns:
#             True if successful, False otherwise
#         """
#         # Delete from MongoDB
#         result = self.mongo_collection.delete_one({"graph_id": graph_id})
#         return result.deleted_count > 0
    
#     def process_directory(self, directory_path: str) -> Dict[str, int]:
#         """
#         Process all Python files in a directory.
        
#         Args:
#             directory_path: Path to the directory
            
#         Returns:
#             Dictionary with counts of processed files and functions
#         """
#         stats = {
#             "files_processed": 0,
#             "functions_found": 0
#         }
        
#         try:
#             # Walk through the directory
#             for root, _, files in os.walk(directory_path):
#                 for file in files:
#                     if file.endswith(".py"):
#                         file_path = os.path.join(root, file)
#                         functions = self.process_python_file(file_path)
#                         stats["files_processed"] += 1
#                         stats["functions_found"] += len(functions)
            
#             return stats
#         except Exception as e:
#             print(f"Error processing directory {directory_path}: {str(e)}")
#             return stats
    
#     def _generate_azure_openai_summary(self, code: str, max_words: int = 30) -> str:
#         """
#         Generate a concise summary of code using Azure OpenAI.
        
#         This method sends the code to Azure OpenAI and requests a concise summary
#         that captures the essence of the function in the specified number of words.
        
#         Args:
#             code: The function code to summarize
#             max_words: Maximum number of words for the summary (default: 30)
            
#         Returns:
#             str: Concise summary of the code
            
#         Note:
#             Requires Azure OpenAI API key and endpoint to be set in environment variables.
#             Falls back to a simple extraction method if API call fails.
#         """
#         # Apply rate limiting
#         self._apply_rate_limit()
        
#         # Check if Azure OpenAI credentials are available
#         if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
#             print("Warning: Azure OpenAI credentials not set. Using fallback summarization.")
#             # Return first line or truncated code as fallback
#             lines = code.split('\n')
#             if lines and len(lines) > 1:
#                 return lines[0].strip()[:100]
#             return code[:100]
        
#         try:
#             # Construct the API URL
#             api_url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
            
#             # Prepare the request payload
#             payload = {
#                 "messages": [
#                     {
#                         "role": "system",
#                         "content": f"You are a code documentation assistant. Your task is to summarize Python functions into concise, informative summaries of {max_words} words or less. Focus on capturing the core functionality and purpose."
#                     },
#                     {
#                         "role": "user",
#                         "content": f"Summarize this Python function in {max_words} words or less:\n\n{code}"
#                     }
#                 ],
#                 "temperature": 0.3,
#                 "max_tokens": 100,
#                 "top_p": 1.0
#             }
            
#             # Set up headers
#             headers = {
#                 "Content-Type": "application/json",
#                 "api-key": AZURE_OPENAI_API_KEY
#             }
            
#             # Make the API call
#             response = requests.post(api_url, headers=headers, json=payload)
#             response.raise_for_status()  # Raise exception for HTTP errors
            
#             # Parse the response
#             result = response.json()
#             summary = result["choices"][0]["message"]["content"].strip()
            
#             return summary
            
#         except Exception as e:
#             print(f"Error calling Azure OpenAI API: {str(e)}")
#             # Fallback to simple extraction
#             lines = code.split('\n')
#             if lines and len(lines) > 1:
#                 return lines[0].strip()[:100]
#             return code[:100]
    
#     def _apply_rate_limit(self):
#         """Apply rate limiting to avoid too many API calls."""
#         current_time = time.time()
#         time_since_last_call = current_time - self.last_api_call
        
#         if time_since_last_call < self.min_request_interval:
#             # Sleep to maintain the minimum interval between requests
#             sleep_time = self.min_request_interval - time_since_last_call
#             time.sleep(sleep_time)
        
#         # Update the last API call time
#         self.last_api_call = time.time()
    
#     def _get_timestamp(self) -> str:
#         """Get current timestamp in ISO format."""
#         from datetime import datetime
#         return datetime.now().isoformat()
    
#     def close(self):
#         """Close database connections."""
#         if self.mongo_client:
#             self.mongo_client.close()




import os
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import networkx as nx
from pymongo import MongoClient
from pymongo.collection import Collection
from extractDocStrings import extract_docstrings_from_directory
from searchInDocString import get_function_docstring
from generateSummary import SummaryGenerator

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")


class DatabaseManager:
    """
    Manages connections and operations for MongoDB.
    Vector database functionality is commented out.
    """
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        self.summary_generator = SummaryGenerator()  # Create an instance of SummaryGenerator
  
        # Initialize connections
        self._init_mongo()

    def _init_mongo(self):
        """Initialize MongoDB connection."""
        try:
            self.mongo_client = MongoClient(MONGO_URI)
            self.mongo_db = self.mongo_client[MONGO_DB_NAME]
            self.mongo_collection = self.mongo_db[MONGO_COLLECTION]
            print(f"Connected to MongoDB: {MONGO_DB_NAME}.{MONGO_COLLECTION}")
        except Exception as e:
            print(f"Error connecting to MongoDB: {str(e)}")
            raise
    
    def store_graph(self, graph: nx.DiGraph, project_name: str, directory: str = None) -> str:
        """
        Store graph data in MongoDB.
        
        Args:
            graph: NetworkX graph object
            project_name: Name of the project
            directory: Optional directory path to extract docstrings from
            
        Returns:
            graph_id: Unique ID for the stored graph
        """
        # Generate a unique ID for this graph
        graph_id = str(uuid.uuid4())
        
        # Extract docstrings if directory is provided
        all_docstrings = {}
        if directory:
            all_docstrings = extract_docstrings_from_directory(directory)
        
        # Store metadata in MongoDB
        metadata = {
            "graph_id": graph_id,
            "project_name": project_name,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "timestamp": self._get_timestamp(),
            "nodes": [],
            "edges": []
        }
        
        # Process nodes with async batch processing
        if directory:
            metadata["nodes"] = asyncio.run(self._process_nodes_async(graph, graph_id, all_docstrings))
        else:
            # Fallback to synchronous processing if no directory is provided
            metadata["nodes"] = self._process_nodes_sync(graph, graph_id)
        
        # Process edges
        metadata["edges"] = self._process_edges(graph, graph_id)
        
        # Store metadata in MongoDB
        self.mongo_collection.insert_one(metadata)
        print(f"Stored graph metadata in MongoDB with ID: {graph_id}")
        
        return graph_id
    
    def _process_nodes_sync(self, graph: nx.DiGraph, graph_id: str) -> List[Dict]:
        """Process nodes synchronously (fallback method)."""
        nodes_data = []
        for node in graph.nodes:
            # Generate a unique ID for this node
            node_id = f"{graph_id}_{node}"
            
            # Get node attributes
            node_attrs = graph.nodes[node]
            node_type = node_attrs.get("type", "unknown")
            
            # Add to nodes data
            nodes_data.append({
                "id": node_id,
                "name": node,
                "type": node_type,
                "attributes": node_attrs,
                "description": ""
            })
        
        return nodes_data
    
    async def _process_nodes_async(self, graph: nx.DiGraph, graph_id: str, all_docstrings: Dict) -> List[Dict]:
        """Process nodes asynchronously with batch processing for summaries."""
        # Prepare node data and collect docstrings for batch processing
        nodes_data = []
        node_docstrings = []
        node_indices = []
        
        for i, node in enumerate(graph.nodes):
            # Generate a unique ID for this node
            node_id = f"{graph_id}_{node}"
            
            # Get node attributes
            node_attrs = graph.nodes[node]
            node_type = node_attrs.get("type", "unknown")
            
            # Add to nodes data
            nodes_data.append({
                "id": node_id,
                "name": node,
                "type": node_type,
                "attributes": node_attrs,
                "description": ""  # Will be filled in later
            })
            
            # Collect docstrings for batch processing
            if isinstance(node, str):
                docstring = get_function_docstring(node, all_docstrings)
                if docstring and docstring != f"Function '{node}' not found.":
                    node_docstrings.append(docstring)
                    node_indices.append(i)
        
        # Batch process docstrings if any were found
        if node_docstrings:
            print(f"Batch processing {len(node_docstrings)} docstrings...")
            summaries = await self.summary_generator.generate_summaries_batch(node_docstrings, 30)
            
            # Update node descriptions with summaries
            for i, summary in enumerate(summaries):
                node_index = node_indices[i]
                nodes_data[node_index]["description"] = summary
        
        return nodes_data
    
    def _process_edges(self, graph: nx.DiGraph, graph_id: str) -> List[Dict]:
        """Process edges and return edge data."""
        edges_data = []
        for u, v, data in graph.edges(data=True):
            # Generate a unique ID for this edge
            edge_id = f"{graph_id}_{u}_{v}"
            
            # Get edge attributes
            relation = data.get("relation", "unknown")
            
            # Add to edges data
            edges_data.append({
                "id": edge_id,
                "source": u,
                "target": v,
                "relation": relation,
                "attributes": data
                # "description": edgeDescription
            })
        
        return edges_data
    
    def get_graph_metadata(self, graph_id: str) -> Optional[Dict]:
        """
        Retrieve graph metadata from MongoDB.
        
        Args:
            graph_id: ID of the graph to retrieve
            
        Returns:
            Metadata dictionary or None if not found
        """
        return self.mongo_collection.find_one({"graph_id": graph_id}, {"_id": 0})
    
    def list_graphs(self) -> List[Dict]:
        """
        List all stored graphs with basic metadata.
        
        Returns:
            List of graph metadata dictionaries
        """
        return list(self.mongo_collection.find({}, {
            "_id": 0,
            "graph_id": 1,
            "project_name": 1,
            "node_count": 1,
            "edge_count": 1,
            "timestamp": 1
        }))
    
    def delete_graph(self, graph_id: str) -> bool:
        """
        Delete a graph from MongoDB.
        
        Args:
            graph_id: ID of the graph to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Delete from MongoDB
        result = self.mongo_collection.delete_one({"graph_id": graph_id})
        return result.deleted_count > 0
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def close(self):
        """Close database connections."""
        if self.mongo_client:
            self.mongo_client.close()
