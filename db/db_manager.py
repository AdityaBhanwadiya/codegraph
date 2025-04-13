import os
import uuid
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import networkx as nx
from pymongo import MongoClient
from scripts.extractDocStrings import extract_docstrings_from_directory
from search.searchInDocString import get_function_docstring
from segregate.segregateDocString import parse_docstring
from db.vector_db_manager import QdrantManager

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")


class DatabaseManager:
    """
    Manages connections and operations for MongoDB and Qdrant vector database.
    """
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        self.vector_db = None
  
        # Initialize connections
        self._init_mongo()
        self._init_vector_db()

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
    def _init_vector_db(self):
        """Initialize vector database connection."""
        try:
            self.vector_db = QdrantManager()
            print("Connected to Qdrant vector database")
        except Exception as e:
            print(f"Error connecting to Qdrant: {str(e)}")
            self.vector_db = None
    
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
        
        # Store embeddings in vector database if available
        if self.vector_db and directory:
            self._store_embeddings(metadata["nodes"], metadata["edges"])
        
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
    
    def _store_embeddings(self, nodes: List[Dict], edges: List[Dict]) -> None:
        """
        Store embeddings for nodes and edges in the vector database.
        
        Args:
            nodes: List of node dictionaries
            edges: List of edge dictionaries
        """
        if not self.vector_db:
            return
        
        # Process nodes with docstrings
        node_ids = []
        node_texts = []
        node_metadata = []
        
        for node in nodes:
            if "docstring_data" in node:
                # Create a text representation of the node
                node_text = f"Node: {node['name']} (Type: {node['type']})\n"
                
                # Add docstring data
                docstring_data = node["docstring_data"]
                node_text += f"Summary: {docstring_data['summary']}\n"
                
                if docstring_data['parameters']:
                    node_text += "Parameters:\n"
                    for param_name, param_desc in docstring_data['parameters'].items():
                        node_text += f"  - {param_name}: {param_desc}\n"
                
                if docstring_data['returns']:
                    node_text += f"Returns: {docstring_data['returns']}\n"
                
                if docstring_data['raises']:
                    node_text += f"Raises: {docstring_data['raises']}\n"
                
                if docstring_data['note']:
                    node_text += f"Note: {docstring_data['note']}\n"
                
                if docstring_data['example']:
                    node_text += f"Example: {docstring_data['example']}\n"
                
                # Add to lists
                node_ids.append(node["id"])
                node_texts.append(node_text)
                node_metadata.append({
                    "id": node["id"],
                    "name": node["name"],
                    "type": node["type"],
                    "docstring_data": docstring_data
                })
        
        # Store node embeddings
        if node_ids:
            print(f"Storing embeddings for {len(node_ids)} nodes...")
            success = self.vector_db.generate_and_store(node_ids, node_texts, node_metadata)
            if success:
                print("Node embeddings stored successfully")
            else:
                print("Failed to store node embeddings")
        
        # Process edges
        edge_ids = []
        edge_texts = []
        edge_metadata = []
        
        for edge in edges:
            # Create a text representation of the edge
            edge_text = f"Edge: {edge['source']} -> {edge['target']} (Relation: {edge['relation']})"
            
            # Add to lists
            edge_ids.append(edge["id"])
            edge_texts.append(edge_text)
            edge_metadata.append({
                "id": edge["id"],
                "source": edge["source"],
                "target": edge["target"],
                "relation": edge["relation"]
            })
        
        # Store edge embeddings
        if edge_ids:
            print(f"Storing embeddings for {len(edge_ids)} edges...")
            success = self.vector_db.generate_and_store(edge_ids, edge_texts, edge_metadata)
            if success:
                print("Edge embeddings stored successfully")
            else:
                print("Failed to store edge embeddings")
    
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
                "description": ""

            })
            
            # Collect docstrings for batch processing
            if isinstance(node, str):
                docstring = get_function_docstring(node, all_docstrings)
                if docstring and docstring != f"Function '{node}' not found.":
                    node_docstrings.append(docstring)
                    node_indices.append(i)
        
        # Process docstrings if any were found
        if node_docstrings:
            print(f"Processing {len(node_docstrings)} docstrings...")
            
            # Update node data with parsed docstrings
            for i, docstring in enumerate(node_docstrings):
                node_index = node_indices[i]
                parsed_docstring = parse_docstring(docstring)
                nodes_data[node_index]["docstring_data"] = parsed_docstring
                # Use the summary from parsed docstring as the description
                nodes_data[node_index]["description"] = parsed_docstring['summary']
        
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
        Delete a graph from MongoDB and vector database.
        
        Args:
            graph_id: ID of the graph to delete
            
        Returns:
            True if successful, False otherwise
        """
        # Delete from MongoDB
        result = self.mongo_collection.delete_one({"graph_id": graph_id})
        mongo_success = result.deleted_count > 0
        
        # Delete from vector database
        vector_db_success = True
        if self.vector_db:
            # Note: This is a simplification. In a real implementation, you would
            # need to delete only the vectors associated with this graph_id.
            # For now, we're just deleting the entire collection.
            vector_db_success = self.vector_db.delete_collection()
        
        return mongo_success and vector_db_success
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def search_by_text(self, query_text: str, top_k: int = 5) -> List[Dict]:
        """
        Search for nodes and edges by text query.
        
        Args:
            query_text: The text query to search for
            top_k: Number of results to return
            
        Returns:
            List of dictionaries containing the search results
        """
        if not self.vector_db:
            return []
        
        return self.vector_db.search_by_text(query_text, top_k)
    
    def close(self):
        """Close database connections."""
        if self.mongo_client:
            self.mongo_client.close()
        
        if self.vector_db:
            self.vector_db.close()
