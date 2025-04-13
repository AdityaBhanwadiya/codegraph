from mcp.server.fastmcp import FastMCP, Context, Image
import networkx as nx
import os
import tempfile
import base64
from typing import List, Dict, Optional, Any
import json
from dotenv import load_dotenv

# Import your existing code modules
from parsers.code_parser import CodeGraphBuilder
from visualize.visualize_graph import draw_graph, _draw_interactive_graph
from db.db_manager import DatabaseManager
from scripts.extractDocStrings import extract_docstrings_from_directory
from search.searchInDocString import get_function_docstring
from db.logging_utils import get_logger

# Set up logger
logger = get_logger("mcp_server")

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(
    "CodeGraphVisualizer",
    dependencies=[
        "networkx", "matplotlib", "pyvis", "pymongo", 
        "sentence-transformers", "python-dotenv", "pygraphviz"
    ]
)

# Initialize database manager
db_manager = DatabaseManager()

@mcp.tool()
def parse_code_directory(directory_path: str, include_builtins: bool = False, include_stdlib: bool = False) -> str:
    """
    Parse a directory of Python code and build a code knowledge graph.
    
    Args:
        directory_path: Path to the directory containing Python code
        include_builtins: Whether to include built-in functions in the graph
        include_stdlib: Whether to include standard library functions in the graph
        
    Returns:
        A JSON string containing information about the graph
    """
    # Validate directory path
    if not os.path.isdir(directory_path):
        return f"Error: '{directory_path}' is not a valid directory."
    
    logger.info(f"Parsing code directory: {directory_path}")
    
    # Create the graph builder with options
    builder = CodeGraphBuilder(
        directory_path,
        exclude_builtins=not include_builtins,
        exclude_stdlib=not include_stdlib
    )
    
    # Parse the project
    graph = builder.parse_project()
    logger.info(f"Parsed project, found {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    
    # Return basic graph info
    return json.dumps({
        "status": "success",
        "directory": directory_path,
        "node_count": len(graph.nodes),
        "edge_count": len(graph.edges),
        "file_count": sum(1 for n, attr in graph.nodes(data=True) if attr.get("type") == "file"),
        "function_count": sum(1 for n, attr in graph.nodes(data=True) if attr.get("type") == "function"),
        "graph_available": True
    })


@mcp.tool()
async def visualize_code_graph_and_save(
    directory_path: str,
    output_path: str,
    layout_type: str = "hierarchical",
    filter_relations: Optional[List[str]] = None,
    include_builtins: bool = False,
    include_stdlib: bool = False,
    ctx: Context = None
) -> str:
    """
    Generate an interactive HTML visualization of a code knowledge graph and save it to a file using the filesystem MCP.
    
    Args:
        directory_path: Path to the directory containing Python code
        output_path: Path where to save the HTML visualization
        layout_type: Type of layout (hierarchical, circular, spring, kamada_kawai)
        filter_relations: List of relation types to include (contains, imports, calls)
        include_builtins: Whether to include built-in functions in the graph
        include_stdlib: Whether to include standard library functions in the graph
        ctx: MCP Context for progress reporting and accessing other MCP services
        
    Returns:
        Information about the saved visualization
    """
    # Validate directory path
    if not os.path.isdir(directory_path):
        return f"Error: '{directory_path}' is not a valid directory."
    
    # Report progress if context is available
    if ctx:
        ctx.info(f"Analyzing code in {directory_path}")
        await ctx.report_progress(0, 100)
    
    logger.info(f"Visualizing code in {directory_path}")
    
    # Create the graph builder with options
    builder = CodeGraphBuilder(
        directory_path,
        exclude_builtins=not include_builtins,
        exclude_stdlib=not include_stdlib
    )
    
    # Parse the project
    if ctx:
        ctx.info("Building code graph")
        await ctx.report_progress(25, 100)
    
    graph = builder.parse_project()
    logger.info(f"Parsed project, building visualization with {len(graph.nodes)} nodes")
    
    # Filter the graph if needed
    if filter_relations:
        valid_relations = ["contains", "imports", "calls"]
        filter_relations = [r for r in filter_relations if r in valid_relations]
        
        logger.info(f"Filtering graph by relations: {filter_relations}")
        
        # Create a filtered copy of the graph
        filtered_graph = nx.DiGraph()
        for n, attrs in graph.nodes(data=True):
            filtered_graph.add_node(n, **attrs)
        
        for u, v, attrs in graph.edges(data=True):
            if attrs.get("relation") in filter_relations:
                filtered_graph.add_edge(u, v, **attrs)
        
        graph = filtered_graph
    
    # Remove isolated nodes (no connections)
    isolated_nodes = list(nx.isolates(graph))
    if isolated_nodes:
        logger.info(f"Removing {len(isolated_nodes)} isolated nodes")
        graph.remove_nodes_from(isolated_nodes)
    
    if ctx:
        ctx.info("Creating visualization")
        await ctx.report_progress(50, 100)
    
    # Create a Pyvis network
    import pyvis.network as net
    network = net.Network(height="800px", width="100%", notebook=False, directed=True)
    
    # Set physics options for better node dragging and edge flexibility
    network.set_options("""
    {
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -2000,
          "centralGravity": 0.1,
          "springLength": 150,
          "springConstant": 0.01,
          "damping": 0.09,
          "avoidOverlap": 1
        },
        "solver": "barnesHut",
        "stabilization": {
          "enabled": true,
          "iterations": 1000,
          "updateInterval": 100,
          "onlyDynamicEdges": false,
          "fit": true
        },
        "maxVelocity": 50,
        "minVelocity": 0.1,
        "timestep": 0.5
      },
      "interaction": {
        "dragNodes": true,
        "dragView": true,
        "zoomView": true,
        "hover": true,
        "navigationButtons": true,
        "keyboard": {
          "enabled": true,
          "speed": {
            "x": 10,
            "y": 10,
            "zoom": 0.02
          },
          "bindToWindow": true
        }
      },
      "edges": {
        "smooth": {
          "enabled": true,
          "type": "dynamic",
          "roundness": 0.5
        },
        "physics": true
      },
      "layout": {
        "improvedLayout": true,
        "hierarchical": {
          "enabled": false
        }
      },
      "manipulation": {
        "enabled": true
      }
    }
    """)
    
    # Add nodes with appropriate colors and sizes
    for node in graph.nodes:
        ntype = graph.nodes[node].get("type", "")
        if ntype == "file":
            color = "#4287f5"  # Blue
            size = 30
            shape = "dot"
        elif ntype == "function":
            color = "#f5a742"  # Orange
            size = 25
            shape = "dot"
        else:
            color = "#aaaaaa"  # Gray
            size = 20
            shape = "dot"
        
        network.add_node(node, label=node, color=color, size=size, shape=shape, title=f"Type: {ntype}")
    
    # Add edges with appropriate colors
    for u, v, data in graph.edges(data=True):
        relation = data.get('relation', '')
        if relation == 'contains':
            color = '#2ecc71'  # Green
        elif relation == 'imports':
            color = '#e74c3c'  # Red
        elif relation == 'calls':
            color = '#9b59b6'  # Purple
        else:
            color = '#95a5a6'  # Gray
        
        network.add_edge(u, v, title=relation, color=color, label=relation)
    
    # Generate HTML string
    html_string = network.generate_html()
    
    if ctx:
        ctx.info("Saving visualization to file using Filesystem MCP")
        await ctx.report_progress(75, 100)
    
    try:
        # Write the HTML content to the file directly
        logger.info(f"Saving visualization to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_string)
        
        if ctx:
            ctx.info("Visualization saved successfully")
            await ctx.report_progress(100, 100)
        
        return json.dumps({
            "status": "success",
            "message": f"Generated HTML visualization saved to {output_path}",
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "file_count": sum(1 for n, attr in graph.nodes(data=True) if attr.get("type") == "file"),
            "function_count": sum(1 for n, attr in graph.nodes(data=True) if attr.get("type") == "function")
        })
    except Exception as e:
        logger.error(f"Error saving visualization: {str(e)}")
        if ctx:
            ctx.info(f"Error saving visualization: {str(e)}")
        
        return json.dumps({
            "status": "error",
            "message": f"Failed to save visualization: {str(e)}"
        })
    
@mcp.tool()
async def store_code_graph(directory_path: str, project_name: str = None, skip_summaries: bool = True, store_embeddings: bool = True) -> str:
    """
    Store a code knowledge graph in the database and optionally create vector embeddings.
    
    Args:
        directory_path: Path to the directory containing Python code
        project_name: Name to identify the project (defaults to directory name)
        skip_summaries: Skip generating summaries to avoid timeouts (default: True)
        store_embeddings: Whether to create and store vector embeddings (default: True)
        
    Returns:
        The graph ID if successful, error message otherwise
    """
    # Validate directory path
    if not os.path.isdir(directory_path):
        return f"Error: '{directory_path}' is not a valid directory."
    
    # Use directory name if project name not provided
    if not project_name:
        project_name = os.path.basename(os.path.abspath(directory_path))
    
    logger.info(f"Storing code graph for project: {project_name}")
    
    # Create the graph builder
    builder = CodeGraphBuilder(directory_path)
    
    try:
        # Parse the project
        graph = builder.parse_project()
        
        # Generate a unique ID for this graph
        import uuid
        graph_id = str(uuid.uuid4())
        logger.info(f"Generated graph ID: {graph_id}")
        
        # Extract docstrings if needed for embeddings or non-skip summaries
        all_docstrings = {}
        if not skip_summaries or store_embeddings:
            logger.info(f"Extracting docstrings from {directory_path}")
            all_docstrings = extract_docstrings_from_directory(directory_path)
        
        # Store metadata in MongoDB
        metadata = {
            "graph_id": graph_id,
            "project_name": project_name,
            "node_count": len(graph.nodes),
            "edge_count": len(graph.edges),
            "timestamp": db_manager._get_timestamp(),
            "nodes": [],
            "edges": []
        }
        
        # Process nodes with docstrings if enabled
        nodes_data = []
        if not skip_summaries and all_docstrings:
            logger.info("Processing nodes with docstrings")
            from search.text_preprocessor import preprocess_docstring_data
            from segregate.segregateDocString import parse_docstring
            
            for node in graph.nodes:
                # Generate a unique ID for this node
                node_id = f"{graph_id}_{node}"
                
                # Get node attributes
                node_attrs = graph.nodes[node]
                node_type = node_attrs.get("type", "unknown")
                
                # Get docstring if available
                node_data = {
                    "id": node_id,
                    "name": node,
                    "type": node_type,
                    "attributes": node_attrs,
                    "description": ""  # Default empty description
                }
                
                # Process docstring for function nodes
                if isinstance(node, str):
                    docstring = get_function_docstring(node, all_docstrings)
                    if docstring and docstring != f"Function '{node}' not found.":
                        # Parse the docstring
                        parsed_docstring = parse_docstring(docstring)
                        
                        # Preprocess the parsed docstring
                        preprocessed_docstring = preprocess_docstring_data(parsed_docstring)
                        
                        # Store both the original and preprocessed versions
                        node_data["docstring_data"] = parsed_docstring
                        node_data["preprocessed_docstring_data"] = preprocessed_docstring
                        
                        # Use the summary from parsed docstring as the description
                        node_data["description"] = preprocessed_docstring.get('summary', '')
                
                nodes_data.append(node_data)
        else:
            # Simplified node processing when skipping summaries
            logger.info("Processing nodes with simplified data (skipping docstrings)")
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
                    "description": ""  # Skip detailed descriptions
                })
        
        metadata["nodes"] = nodes_data
        logger.info(f"Processed {len(nodes_data)} nodes")
        
        # Process edges
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
        
        metadata["edges"] = edges_data
        logger.info(f"Processed {len(edges_data)} edges")
        
        # Store metadata in MongoDB
        db_manager.mongo_collection.insert_one(metadata)
        
        # Store vector embeddings if enabled
        if store_embeddings and db_manager.vector_db:
            logger.info("Storing vector embeddings for nodes and edges")
            
            # Create lists for vector storage
            node_ids = []
            node_texts = []
            node_metadata = []
            
            # Process nodes for vector embeddings - include ALL nodes, even without docstrings
            for node in nodes_data:
                # Create a node text representation for embedding
                node_name = node["name"]
                node_type = node["type"]
                base_text = f"Node: {node_name} (Type: {node_type})"
                
                # If we have docstring data, use it to enrich the text
                if "preprocessed_docstring_data" in node:
                    from search.text_preprocessor import get_combined_text_for_embedding
                    preprocessed_data = node["preprocessed_docstring_data"]
                    docstring_text = get_combined_text_for_embedding(preprocessed_data)
                    
                    # Combine base node info with docstring data
                    node_text = f"{base_text}\n{docstring_text}"
                else:
                    # Otherwise just use the base text
                    node_text = base_text
                
                # Add to lists
                node_ids.append(node["id"])
                node_texts.append(node_text)
                
                # Prepare metadata - include all available node information
                metadata = {
                    "id": node["id"],
                    "name": node["name"],
                    "type": node["type"]
                }
                
                # Add docstring data if available
                if "docstring_data" in node:
                    metadata["docstring_data"] = node["docstring_data"]
                
                # Add preprocessed docstring data if available
                if "preprocessed_docstring_data" in node:
                    metadata["preprocessed_docstring_data"] = node["preprocessed_docstring_data"]
                
                node_metadata.append(metadata)
            
            # Store node embeddings if there are any
            if node_ids:
                logger.info(f"Storing vector embeddings for {len(node_ids)} nodes")
                success = db_manager.vector_db.generate_and_store(node_ids, node_texts, node_metadata)
                if success:
                    logger.info("Successfully stored node vector embeddings")
                else:
                    logger.warning("Failed to store node vector embeddings")
            
            # Process edges for vector embeddings
            edge_ids = []
            edge_texts = []
            edge_metadata = []
            
            for edge in edges_data:
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
            
            # Store edge embeddings if there are any
            if edge_ids:
                logger.info(f"Storing vector embeddings for {len(edge_ids)} edges")
                success = db_manager.vector_db.generate_and_store(edge_ids, edge_texts, edge_metadata)
                if success:
                    logger.info("Successfully stored edge vector embeddings")
                else:
                    logger.warning("Failed to store edge vector embeddings")
        
        # Return success response
        result = {
            "status": "success",
            "message": f"Graph stored with ID: {graph_id}",
            "graph_id": graph_id,
            "project_name": project_name,
            "nodes_count": len(nodes_data),
            "edges_count": len(edges_data)
        }
        
        # Add note about skipped summaries if applicable
        if skip_summaries:
            result["note"] = "Summaries were skipped to avoid timeouts. Node descriptions may be empty."
        
        # Add note about vector embeddings if applicable
        if store_embeddings and db_manager.vector_db:
            result["vector_embeddings"] = "Vector embeddings were generated and stored for semantic search capabilities."
        
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to store graph: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Failed to store graph: {str(e)}"
        })
    
@mcp.tool()
def delete_graph(graph_id: str) -> str:
    """
    Delete a code knowledge graph from the database.
    
    Args:
        graph_id: ID of the graph to delete
        
    Returns:
        Success or error message
    """
    try:
        logger.info(f"Deleting graph with ID: {graph_id}")
        success = db_manager.delete_graph(graph_id)
        if success:
            logger.info(f"Graph {graph_id} deleted successfully")
            return json.dumps({
                "status": "success",
                "message": f"Graph {graph_id} deleted successfully."
            })
        else:
            logger.warning(f"Failed to delete graph {graph_id}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to delete graph {graph_id}."
            })
    except Exception as e:
        logger.error(f"Error deleting graph: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error deleting graph: {str(e)}"
        })

@mcp.tool()
def search_vector_db(query_text: str, top_k: int = 5, project_name: str = None, debug: bool = False) -> str:
    """
    Search for nodes and edges in the vector database using semantic similarity.
    
    Args:
        query_text: The text query to search for. Can be a question, description, or keywords.
        top_k: Number of results to return (default: 5)
        project_name: Optional project name to filter results by
        debug: If True, includes debugging information in the response
        
    Returns:
        JSON string containing search results with similarity scores
    """
    try:
        # Validate input
        if not query_text or not query_text.strip():
            return json.dumps({
                "status": "error",
                "message": "Query text cannot be empty."
            })
        
        logger.info(f"Searching vector DB for: '{query_text}'")
        
        # Debug information
        debug_info = {
            "raw_query": query_text,
            "filtered_out_count": 0,
            "total_raw_results": 0,
            "project_name_filter": project_name
        }
        
        # Use the existing search_by_text method from DatabaseManager
        from search.text_preprocessor import preprocess_text
        preprocessed_query = preprocess_text(query_text)
        if debug:
            debug_info["preprocessed_query"] = preprocessed_query
            
        results = db_manager.search_by_text(query_text, top_k * 2)  # Request more results to compensate for filtering
        
        # If no results found
        if not results:
            logger.info("No matching results found")
            return json.dumps({
                "status": "success", 
                "message": "No matching results found.",
                "results": [],
                "debug_info": debug_info if debug else None
            })
            
        debug_info["total_raw_results"] = len(results)
        if debug:
            debug_info["raw_results"] = [{
                "id": r.get("id", "unknown"),
                "score": r.get("score", 0),
                "metadata_keys": list(r.get("metadata", {}).keys())
            } for r in results]
        
        # Process and format the results
        formatted_results = []
        filtered_out = 0
        for result in results:
            metadata = result.get("metadata", {})
            result_type = "node" if "type" in metadata else "edge"
            
            # Filter by project_name if specified
            if project_name and "id" in result:
                # Extract graph_id from the result ID (format: graph_id_node_name)
                parts = result["id"].split("_", 1)
                if len(parts) > 1:
                    graph_id = parts[0]
                    # Get graph metadata
                    graph_metadata = db_manager.get_graph_metadata(graph_id)
                    if graph_metadata and graph_metadata.get("project_name") != project_name:
                        filtered_out += 1
                        if debug:
                            if "filtered_items" not in debug_info:
                                debug_info["filtered_items"] = []
                            debug_info["filtered_items"].append({
                                "id": result.get("id", "unknown"),
                                "graph_id": graph_id,
                                "project_name": graph_metadata.get("project_name") if graph_metadata else "unknown"
                            })
                        continue
        
        debug_info["filtered_out_count"] = filtered_out
        
        # Process and format the results
        for result in results:
            metadata = result.get("metadata", {})
            result_type = "node" if "type" in metadata else "edge"
            
            # Format node result
            if result_type == "node":
                formatted_result = {
                    "type": result_type,
                    "name": metadata.get("name", ""),
                    "node_type": metadata.get("type", ""),
                    "similarity_score": result.get("score", 0),
                    "id": result.get("id", "")
                }
                
                # Add docstring information if available
                if "docstring_data" in metadata:
                    docstring = metadata["docstring_data"]
                    formatted_result["summary"] = docstring.get("summary", "")
                    
                    # Include parameters if they exist
                    if docstring.get("parameters"):
                        formatted_result["parameters"] = docstring.get("parameters", {})
                    
                    # Include return info if it exists
                    if docstring.get("returns"):
                        formatted_result["returns"] = docstring.get("returns", "")
            
            # Format edge result
            else:
                formatted_result = {
                    "type": result_type,
                    "source": metadata.get("source", ""),
                    "target": metadata.get("target", ""),
                    "relation": metadata.get("relation", ""),
                    "similarity_score": result.get("score", 0),
                    "id": result.get("id", "")
                }
            
            formatted_results.append(formatted_result)
        
        logger.info(f"Found {len(formatted_results)} results")
        
        return json.dumps({
            "status": "success",
            "message": f"Found {len(formatted_results)} results",
            "results": formatted_results,
            "debug_info": debug_info if debug else None
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Error searching vector database: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"Error searching vector database: {str(e)}"
        })
# Initialize the MCP server
if __name__ == "__main__":
    logger.info("Starting CodeGraphVisualizer MCP server")
    mcp.run()
