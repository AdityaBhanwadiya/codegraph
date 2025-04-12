import os
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
import networkx as nx
from pymongo import MongoClient
from pymongo.collection import Collection
# from sentence_transformers import SentenceTransformer
# import pinecone

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

# Pinecone connection - commented out
# PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
# PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
# PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "code-graph-embeddings")

# Embedding model - commented out
# EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
# EMBEDDING_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

class DatabaseManager:
    """
    Manages connections and operations for MongoDB.
    Vector database functionality is commented out.
    """
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.mongo_collection = None
        # self.pinecone_index = None
        # self.embedding_model = None
        
        # Initialize connections
        self._init_mongo()
        # self._init_pinecone()
        # self._init_embedding_model()
    
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
    
    # def _init_pinecone(self):
    #     """Initialize Pinecone connection."""
    #     if not PINECONE_API_KEY:
    #         print("Warning: PINECONE_API_KEY not set. Vector database operations will not work.")
    #         return
    #     
    #     try:
    #         pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
    #         
    #         # Check if index exists, create if it doesn't
    #         if PINECONE_INDEX_NAME not in pinecone.list_indexes():
    #             pinecone.create_index(
    #                 name=PINECONE_INDEX_NAME,
    #                 dimension=EMBEDDING_DIMENSION,
    #                 metric="cosine"
    #             )
    #             print(f"Created Pinecone index: {PINECONE_INDEX_NAME}")
    #         
    #         self.pinecone_index = pinecone.Index(PINECONE_INDEX_NAME)
    #         print(f"Connected to Pinecone index: {PINECONE_INDEX_NAME}")
    #     except Exception as e:
    #         print(f"Error connecting to Pinecone: {str(e)}")
    #         self.pinecone_index = None
    
    # def _init_embedding_model(self):
    #     """Initialize the embedding model."""
    #     try:
    #         self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    #         print(f"Loaded embedding model: {EMBEDDING_MODEL}")
    #     except Exception as e:
    #         print(f"Error loading embedding model: {str(e)}")
    #         raise
    
    # def generate_embedding(self, text: str) -> List[float]:
    #     """Generate embedding for a text string."""
    #     if not self.embedding_model:
    #         raise ValueError("Embedding model not initialized")
    #     
    #     return self.embedding_model.encode(text).tolist()
    
    def store_graph(self, graph: nx.DiGraph, project_name: str) -> str:
        """
        Store graph data in MongoDB.
        
        Args:
            graph: NetworkX graph object
            project_name: Name of the project
            
        Returns:
            graph_id: Unique ID for the stored graph
        """
        # Generate a unique ID for this graph
        graph_id = str(uuid.uuid4())
        
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
        
        # Process nodes
        for node in graph.nodes:
            # Generate a unique ID for this node
            node_id = f"{graph_id}_{node}"
            
            # Get node attributes
            node_attrs = graph.nodes[node]
            node_type = node_attrs.get("type", "unknown")
            
            # Add to MongoDB metadata
            metadata["nodes"].append({
                "id": node_id,
                "name": node,
                "type": node_type,
                "attributes": node_attrs
            })
        
        # Process edges
        for u, v, data in graph.edges(data=True):
            # Generate a unique ID for this edge
            edge_id = f"{graph_id}_{u}_{v}"
            
            # Get edge attributes
            relation = data.get("relation", "unknown")
            
            # Add to MongoDB metadata
            metadata["edges"].append({
                "id": edge_id,
                "source": u,
                "target": v,
                "relation": relation,
                "attributes": data
            })
        
        # Store metadata in MongoDB
        self.mongo_collection.insert_one(metadata)
        print(f"Stored graph metadata in MongoDB with ID: {graph_id}")
        
        return graph_id
    
    def get_graph_metadata(self, graph_id: str) -> Optional[Dict]:
        """
        Retrieve graph metadata from MongoDB.
        
        Args:
            graph_id: ID of the graph to retrieve
            
        Returns:
            Metadata dictionary or None if not found
        """
        return self.mongo_collection.find_one({"graph_id": graph_id}, {"_id": 0})
    
    # def search_similar_nodes(self, query_text: str, top_k: int = 5, graph_id: Optional[str] = None) -> List[Dict]:
    #     """
    #     Search for nodes similar to the query text.
    #     
    #     Args:
    #         query_text: Text to search for
    #         top_k: Number of results to return
    #         graph_id: Optional graph ID to filter results
    #         
    #     Returns:
    #         List of similar nodes with metadata
    #     """
    #     if not self.pinecone_index:
    #         raise ValueError("Pinecone not initialized")
    #     
    #     # Generate embedding for query
    #     query_embedding = self.generate_embedding(query_text)
    #     
    #     # Prepare filter if graph_id is provided
    #     filter_dict = {"is_node": True}
    #     if graph_id:
    #         filter_dict["graph_id"] = graph_id
    #     
    #     # Query Pinecone
    #     results = self.pinecone_index.query(
    #         vector=query_embedding,
    #         top_k=top_k,
    #         namespace="nodes",
    #         filter=filter_dict,
    #         include_metadata=True
    #     )
    #     
    #     return results.get("matches", [])
    
    # def search_similar_edges(self, query_text: str, top_k: int = 5, graph_id: Optional[str] = None) -> List[Dict]:
    #     """
    #     Search for edges similar to the query text.
    #     
    #     Args:
    #         query_text: Text to search for
    #         top_k: Number of results to return
    #         graph_id: Optional graph ID to filter results
    #         
    #     Returns:
    #         List of similar edges with metadata
    #     """
    #     if not self.pinecone_index:
    #         raise ValueError("Pinecone not initialized")
    #     
    #     # Generate embedding for query
    #     query_embedding = self.generate_embedding(query_text)
    #     
    #     # Prepare filter if graph_id is provided
    #     filter_dict = {"is_edge": True}
    #     if graph_id:
    #         filter_dict["graph_id"] = graph_id
    #     
    #     # Query Pinecone
    #     results = self.pinecone_index.query(
    #         vector=query_embedding,
    #         top_k=top_k,
    #         namespace="edges",
    #         filter=filter_dict,
    #         include_metadata=True
    #     )
    #     
    #     return results.get("matches", [])
    
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
