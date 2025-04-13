import os
import abc
import uuid
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EmbeddingGenerator(abc.ABC):
    """
    Abstract base class for generating embeddings from text.
    This follows the Interface Segregation Principle by providing a focused interface.
    """
    @abc.abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            A list of floats representing the embedding vector
        """
        pass
    
    @abc.abstractmethod
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for a batch of texts.
        
        Args:
            texts: A list of texts to generate embeddings for
            
        Returns:
            A list of embedding vectors
        """
        pass

class SentenceTransformerEmbedding(EmbeddingGenerator):
    """
    Implementation of EmbeddingGenerator using sentence-transformers.
    """
    def __init__(self, model_name: str = None):
        """
        Initialize the embedding generator with the specified model.
        
        Args:
            model_name: Name of the sentence-transformer model to use
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Please install it with 'pip install sentence-transformers'"
            )
        
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = SentenceTransformer(self.model_name)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text.
        
        Args:
            text: The text to generate an embedding for
            
        Returns:
            A list of floats representing the embedding vector
        """
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for a batch of texts.
        
        Args:
            texts: A list of texts to generate embeddings for
            
        Returns:
            A list of embedding vectors
        """
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

class VectorDBManager(abc.ABC):
    """
    Abstract base class for vector database operations.
    This follows the Interface Segregation Principle by providing a focused interface.
    """
    @abc.abstractmethod
    def store_vectors(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> bool:
        """
        Store vectors in the vector database.
        
        Args:
            ids: List of unique IDs for the vectors
            vectors: List of embedding vectors
            metadata: List of metadata dictionaries for the vectors
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def search_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the vector database.
        
        Args:
            query_vector: The query vector to search for
            top_k: Number of results to return
            
        Returns:
            List of dictionaries containing the search results
        """
        pass
    
    @abc.abstractmethod
    def delete_collection(self) -> bool:
        """
        Delete the vector collection.
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def close(self) -> None:
        """Close the vector database connection."""
        pass

class QdrantManager(VectorDBManager):
    """
    Implementation of VectorDBManager using Qdrant.
    """
    def __init__(self, embedding_generator: EmbeddingGenerator = None):
        """
        Initialize the Qdrant manager with the specified embedding generator.
        
        Args:
            embedding_generator: An instance of EmbeddingGenerator
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
        except ImportError:
            raise ImportError(
                "qdrant-client is not installed. "
                "Please install it with 'pip install qdrant-client'"
            )
        
        # Store the imports for later use
        self.models = models
        
        # Get Qdrant configuration from environment variables
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION")
        
        # Initialize the embedding generator
        self.embedding_generator = embedding_generator or SentenceTransformerEmbedding()
        
        # Get the vector size from the embedding model
        self.vector_size = len(self.embedding_generator.generate_embedding("test"))
        
        # Initialize the Qdrant client
        if self.qdrant_api_key:
            # Using Qdrant Cloud with API key
            self.client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
            print(f"Connected to Qdrant Cloud at {self.qdrant_url}")
        else:
            # Using local Qdrant instance
            self.client = QdrantClient(url=self.qdrant_url)
            print(f"Connected to local Qdrant instance at {self.qdrant_url}")
        
        # Create the collection if it doesn't exist
        self._create_collection_if_not_exists()
    
    def _create_collection_if_not_exists(self) -> None:
        """Create the Qdrant collection if it doesn't exist."""
        from qdrant_client.http.exceptions import UnexpectedResponse
        
        try:
            # Check if the collection exists
            self.client.get_collection(self.qdrant_collection)
            print(f"Using existing Qdrant collection: {self.qdrant_collection}")
        except (UnexpectedResponse, ValueError):
            # Create the collection if it doesn't exist
            self.client.create_collection(
                collection_name=self.qdrant_collection,
                vectors_config=self.models.VectorParams(
                    size=self.vector_size,
                    distance=self.models.Distance.COSINE
                )
            )
            print(f"Created new Qdrant collection: {self.qdrant_collection}")
    
    def _generate_deterministic_id(self, metadata: Dict[str, Any]) -> int:
        """
        Generate a deterministic ID based on the content of the metadata.
        This ensures that the same data gets the same ID across different runs.
        
        Args:
            metadata: The metadata dictionary for the vector
            
        Returns:
            A deterministic integer ID
        """
        # Create a deterministic string representation of the metadata
        # We'll use the name and type for nodes, or source/target/relation for edges
        if 'type' in metadata:  # Node
            content_key = f"node:{metadata['name']}:{metadata['type']}"
            
            # If it's a function with a docstring, include a hash of the docstring summary
            if metadata.get('type') == 'function' and 'docstring_data' in metadata:
                docstring_summary = metadata['docstring_data'].get('summary', '')
                content_key += f":{docstring_summary}"
        else:  # Edge
            content_key = f"edge:{metadata.get('source', '')}:{metadata.get('target', '')}:{metadata.get('relation', '')}"
        
        # Hash the content key to get a deterministic integer ID
        # Use a large modulus to avoid collisions
        hash_value = int(hashlib.md5(content_key.encode()).hexdigest(), 16) % (2**63)
        return hash_value
    
    def store_vectors(self, ids: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> bool:
        """
        Store vectors in Qdrant.
        
        Args:
            ids: List of unique IDs for the vectors
            vectors: List of embedding vectors
            metadata: List of metadata dictionaries for the vectors
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create points to upsert
            points = []
            for id_str, vector, meta in zip(ids, vectors, metadata):
                # Generate a deterministic ID based on the content
                deterministic_id = self._generate_deterministic_id(meta)
                
                # Store the original ID in the metadata
                meta['original_id'] = id_str
                
                # Create the point
                points.append(
                    self.models.PointStruct(
                        id=deterministic_id,
                        vector=vector,
                        payload=meta
                    )
                )
            
            # Upsert the points
            self.client.upsert(
                collection_name=self.qdrant_collection,
                points=points
            )
            
            return True
        except Exception as e:
            print(f"Error storing vectors in Qdrant: {str(e)}")
            return False
    
    def search_vectors(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in Qdrant.
        
        Args:
            query_vector: The query vector to search for
            top_k: Number of results to return
            
        Returns:
            List of dictionaries containing the search results
        """
        try:
            # Search for similar vectors
            search_result = self.client.search(
                collection_name=self.qdrant_collection,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True
            )
            
            # Format the results
            results = []
            for scored_point in search_result:
                # Get the original ID from the metadata
                original_id = scored_point.payload.get('original_id', str(scored_point.id))
                
                # Remove the original_id from the metadata to avoid duplication
                payload = dict(scored_point.payload)
                if 'original_id' in payload:
                    del payload['original_id']
                
                results.append({
                    "id": original_id,
                    "score": scored_point.score,
                    "metadata": payload
                })
            
            return results
        except Exception as e:
            print(f"Error searching vectors in Qdrant: {str(e)}")
            return []
    
    def delete_collection(self) -> bool:
        """
        Delete the Qdrant collection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(collection_name=self.qdrant_collection)
            return True
        except Exception as e:
            print(f"Error deleting Qdrant collection: {str(e)}")
            return False
    
    def close(self) -> None:
        """Close the Qdrant client connection."""
        # Qdrant client doesn't have a close method, but we include this for interface compatibility
        pass
    
    def generate_and_store(self, ids: List[str], texts: List[str], metadata: List[Dict[str, Any]]) -> bool:
        """
        Generate embeddings for texts and store them in Qdrant.
        
        Args:
            ids: List of unique IDs for the vectors
            texts: List of texts to generate embeddings for
            metadata: List of metadata dictionaries for the vectors
            
        Returns:
            True if successful, False otherwise
        """
        # Generate embeddings
        vectors = self.embedding_generator.generate_embeddings_batch(texts)
        
        # Store vectors
        return self.store_vectors(ids, vectors, metadata)
    
    def search_by_text(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar vectors by text query.
        
        Args:
            query_text: The text query to search for (already preprocessed)
            top_k: Number of results to return
            
        Returns:
            List of dictionaries containing the search results
        """
        # Note: The query_text is expected to be already preprocessed by the DatabaseManager
        
        # Generate embedding for the preprocessed query text
        query_vector = self.embedding_generator.generate_embedding(query_text)
        
        # Search for similar vectors
        return self.search_vectors(query_vector, top_k)
