import os
import uuid
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import networkx as nx
from pymongo import MongoClient
from scripts.extractDocStrings import extract_docstrings_from_directory
from search.searchInDocString import get_function_docstring
from summarize.generateSummary import SummaryGenerator

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
