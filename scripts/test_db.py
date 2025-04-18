#!/usr/bin/env python3
"""
Test script for database functionality.
This script demonstrates how to use the DatabaseManager class to store and retrieve graph data.
"""

import os
import sys
import networkx as nx

# Add the parent directory to the Python path so modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.db_manager import DatabaseManager
from db.vector_db_manager import QdrantManager

def create_sample_graph():
    """Create a sample graph for testing."""
    G = nx.DiGraph()
    
    # Add file nodes
    G.add_node("app.py", type="file")
    G.add_node("models.py", type="file")
    G.add_node("utils.py", type="file")
    
    # Add function nodes
    G.add_node("main", type="function")
    G.add_node("create_user", type="function")
    G.add_node("get_user", type="function")
    G.add_node("format_date", type="function")
    G.add_node("validate_email", type="function")
    
    # Add file-function relationships (contains)
    G.add_edge("app.py", "main", relation="contains")
    G.add_edge("models.py", "create_user", relation="contains")
    G.add_edge("models.py", "get_user", relation="contains")
    G.add_edge("utils.py", "format_date", relation="contains")
    G.add_edge("utils.py", "validate_email", relation="contains")
    
    # Add file-file relationships (imports)
    G.add_edge("app.py", "models.py", relation="imports")
    G.add_edge("app.py", "utils.py", relation="imports")
    G.add_edge("models.py", "utils.py", relation="imports")
    
    # Add function-function relationships (calls)
    G.add_edge("main", "create_user", relation="calls")
    G.add_edge("main", "get_user", relation="calls")
    G.add_edge("create_user", "validate_email", relation="calls")
    G.add_edge("get_user", "format_date", relation="calls")
    
    return G

def test_store_graph():
    """Test storing a graph in the database."""
    db_manager = DatabaseManager()
    graph = create_sample_graph()
    
    print(f"Created sample graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    
    graph_id = db_manager.store_graph(graph, "Sample Project")
    print(f"Graph stored with ID: {graph_id}")
    
    return graph_id

def test_get_metadata(graph_id):
    """Test retrieving graph metadata."""
    db_manager = DatabaseManager()
    metadata = db_manager.get_graph_metadata(graph_id)
    
    if metadata:
        print("\nGraph Metadata:")
        print(f"Project: {metadata['project_name']}")
        print(f"Nodes: {metadata['node_count']}")
        print(f"Edges: {metadata['edge_count']}")
        print(f"Timestamp: {metadata['timestamp']}")
        
        print("\nNodes:")
        for node in metadata['nodes'][:3]:  # Show first 3 nodes
            print(f"- {node['name']} (Type: {node['type']})")
        if len(metadata['nodes']) > 3:
            print(f"... and {len(metadata['nodes']) - 3} more")
        
        print("\nEdges:")
        for edge in metadata['edges'][:3]:  # Show first 3 edges
            print(f"- {edge['source']} -> {edge['target']} (Relation: {edge['relation']})")
        if len(metadata['edges']) > 3:
            print(f"... and {len(metadata['edges']) - 3} more")
    else:
        print(f"No metadata found for graph ID: {graph_id}")

def test_vector_search():
    """Test searching with vector database."""
    db_manager = DatabaseManager()
    
    queries = [
        "function that validates email",
        "file that contains user functions",
        "utility functions"
    ]
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        results = db_manager.search_by_text(query, top_k=3)
        
        if results:
            for i, result in enumerate(results):
                print(f"{i+1}. Score: {result['score']:.4f}")
                
                # Check if this is a node or edge result
                metadata = result['metadata']
                if 'type' in metadata:  # Node
                    print(f"Node: {metadata['name']} (Type: {metadata['type']})")
                    
                    if 'docstring_data' in metadata:
                        docstring = metadata['docstring_data']
                        print(f"Summary: {docstring['summary']}")
                else:  # Edge
                    print(f"Edge: {metadata['source']} -> {metadata['target']} (Relation: {metadata['relation']})")
        else:
            print("No results found")

def test_list_graphs():
    """Test listing all graphs."""
    db_manager = DatabaseManager()
    graphs = db_manager.list_graphs()
    
    if graphs:
        print("\nStored Graphs:")
        for graph in graphs:
            print(f"ID: {graph['graph_id']}")
            print(f"  Project: {graph['project_name']}")
            print(f"  Nodes: {graph['node_count']}, Edges: {graph['edge_count']}")
            print(f"  Created: {graph['timestamp']}")
            print()
    else:
        print("No graphs found in the database")

def main():
    """Main function to run all tests."""
    print("=== Testing Database Functionality ===")
    
    # Check if MongoDB is configured
    if not os.getenv("MONGO_URI"):
        print("Warning: MONGO_URI not set. Using default: mongodb://localhost:27017")
    
    # Run tests
    print("\n--- Storing Graph ---")
    graph_id = test_store_graph()
    
    print("\n--- Retrieving Metadata ---")
    test_get_metadata(graph_id)
    
    print("\n--- Vector Database Search ---")
    test_vector_search()
    
    print("\n--- Listing Graphs ---")
    test_list_graphs()
    
    print("\nTests completed!")

if __name__ == "__main__":
    main()
