from mcp.server.fastmcp import FastMCP, Context, Image
import networkx as nx
import os
import tempfile
import base64
from typing import List, Dict, Optional, Any
import json
from dotenv import load_dotenv

# Import your existing code modules
from code_parser import CodeGraphBuilder
from visualize_graph import draw_graph, _draw_interactive_graph
from db_manager import DatabaseManager
from extractDocStrings import extract_docstrings_from_directory
from searchInDocString import get_function_docstring

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
    
    # Create the graph builder with options
    builder = CodeGraphBuilder(
        directory_path,
        exclude_builtins=not include_builtins,
        exclude_stdlib=not include_stdlib
    )
    
    # Parse the project
    graph = builder.parse_project()
    
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
    
    # Filter the graph if needed
    if filter_relations:
        valid_relations = ["contains", "imports", "calls"]
        filter_relations = [r for r in filter_relations if r in valid_relations]
        
        # Create a filtered copy of the graph
        filtered_graph = nx.DiGraph()
        for n, attrs in graph.nodes(data=True):
            filtered_graph.add_node(n, **attrs)
        
        for u, v, attrs in graph.edges(data=True):
            if attrs.get("relation") in filter_relations:
                filtered_graph.add_edge(u, v, **attrs)
        
        graph = filtered_graph
    
    # Remove isolated nodes (no connections)
    graph.remove_nodes_from(list(nx.isolates(graph)))
    
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
        if ctx:
            ctx.info(f"Error saving visualization: {str(e)}")
        
        return json.dumps({
            "status": "error",
            "message": f"Failed to save visualization: {str(e)}"
        })
    
@mcp.tool()
async def store_code_graph(directory_path: str, project_name: str = None, skip_summaries: bool = True) -> str:
    """
    Store a code knowledge graph in the database.
    
    Args:
        directory_path: Path to the directory containing Python code
        project_name: Name to identify the project (defaults to directory name)
        skip_summaries: Skip generating summaries to avoid timeouts (default: True)
        
    Returns:
        The graph ID if successful, error message otherwise
    """
    # Validate directory path
    if not os.path.isdir(directory_path):
        return f"Error: '{directory_path}' is not a valid directory."
    
    # Use directory name if project name not provided
    if not project_name:
        project_name = os.path.basename(os.path.abspath(directory_path))
    
    # Create the graph builder
    builder = CodeGraphBuilder(directory_path)
    
    try:
        # Parse the project
        graph = builder.parse_project()
        
        # Generate a unique ID for this graph
        import uuid
        graph_id = str(uuid.uuid4())
        
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
        
        # Process nodes - simplified to avoid timeouts
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
                "description": ""  # Skip detailed descriptions for now
            })
        
        metadata["nodes"] = nodes_data
        
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
        
        # Store metadata in MongoDB
        db_manager.mongo_collection.insert_one(metadata)
        
        return json.dumps({
            "status": "success",
            "message": f"Graph stored with ID: {graph_id}",
            "graph_id": graph_id,
            "project_name": project_name,
            "note": "Summaries were skipped to avoid timeouts. Node descriptions are empty."
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to store graph: {str(e)}"
        })
    
@mcp.tool()
def list_stored_graphs() -> str:
    """
    List all code knowledge graphs stored in the database.
    
    Returns:
        JSON string containing information about stored graphs
    """
    try:
        graphs = db_manager.list_graphs()
        return json.dumps({
            "status": "success",
            "count": len(graphs),
            "graphs": graphs
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to list graphs: {str(e)}"
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
        success = db_manager.delete_graph(graph_id)
        if success:
            return json.dumps({
                "status": "success",
                "message": f"Graph {graph_id} deleted successfully."
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to delete graph {graph_id}."
            })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Error deleting graph: {str(e)}"
        })

@mcp.resource("graph://{directory}")
def get_graph_summary(directory: str) -> str:
    """
    Get a summary of the code graph for a directory.
    
    Args:
        directory: Path to the directory containing Python code
        
    Returns:
        A textual summary of the code graph
    """
    # Validate directory path
    if not os.path.isdir(directory):
        return f"Error: '{directory}' is not a valid directory."
    
    # Create the graph builder
    builder = CodeGraphBuilder(directory)
    
    # Parse the project
    graph = builder.parse_project()
    
    # Calculate stats
    file_nodes = sum(1 for n, attr in graph.nodes(data=True) if attr.get("type") == "file")
    function_nodes = sum(1 for n, attr in graph.nodes(data=True) if attr.get("type") == "function")
    contains_edges = sum(1 for _, _, attr in graph.edges(data=True) if attr.get("relation") == "contains")
    imports_edges = sum(1 for _, _, attr in graph.edges(data=True) if attr.get("relation") == "imports")
    calls_edges = sum(1 for _, _, attr in graph.edges(data=True) if attr.get("relation") == "calls")
    
    # Extract docstrings for top-level functions
    all_docstrings = extract_docstrings_from_directory(directory)
    
    # Find important nodes (files with most functions and functions with most calls)
    file_importance = {}
    for u, v, attr in graph.edges(data=True):
        if attr.get("relation") == "contains":
            file_importance[u] = file_importance.get(u, 0) + 1
    
    function_importance = {}
    for u, v, attr in graph.edges(data=True):
        if attr.get("relation") == "calls":
            function_importance[u] = function_importance.get(u, 0) + 1
    
    # Get top files and functions
    top_files = sorted(file_importance.items(), key=lambda x: x[1], reverse=True)[:5]
    top_functions = sorted(function_importance.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Build summary
    summary = f"Code Knowledge Graph Summary for {directory}\n\n"
    summary += f"Total nodes: {len(graph.nodes)} ({file_nodes} files, {function_nodes} functions)\n"
    summary += f"Total edges: {len(graph.edges)} ({contains_edges} contains, {imports_edges} imports, {calls_edges} calls)\n\n"
    
    summary += "Top Files (by number of functions):\n"
    for file, count in top_files:
        summary += f"- {file}: {count} functions\n"
    
    summary += "\nTop Functions (by number of outgoing calls):\n"
    for func, count in top_functions:
        docstring = get_function_docstring(func, all_docstrings)
        if docstring and not docstring.startswith("Function"):
            # Only show first line of docstring
            docstring_first_line = docstring.split("\n")[0].strip()
            summary += f"- {func}: {count} calls - {docstring_first_line}\n"
        else:
            summary += f"- {func}: {count} calls\n"
    
    return summary

@mcp.prompt()
def analyze_code_structure(directory: str) -> str:
    """
    Create a prompt for analyzing code structure in a directory.
    
    Args:
        directory: Path to the directory containing Python code
    """
    return f"""
I'd like you to analyze the code structure in the directory: {directory}

Please help me understand:
1. The high-level architecture of the codebase
2. Key functions and their relationships
3. File dependencies and import patterns
4. Any potential code organization issues or improvements

Use the code knowledge graph tools to visualize and explore the codebase.
"""

# Initialize the MCP server
if __name__ == "__main__":
    mcp.run()
