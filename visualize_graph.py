import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from networkx.drawing.nx_agraph import graphviz_layout
import plotly.graph_objects as go
import pyvis.network as net
import os
import tempfile
import webbrowser

def draw_graph(graph, interactive=True, layout_type="hierarchical", filter_relations=None, save_path=None):
    """
    Draw a graph visualization with various layout options and filtering.
    
    Args:
        graph: NetworkX graph object
        interactive: Whether to use interactive visualization (True) or static (False)
        layout_type: Type of layout ('hierarchical', 'circular', 'spring', 'kamada_kawai')
        filter_relations: List of relation types to include (None for all)
        save_path: Path to save the image (None to display)
    """
    # Create a copy of the graph for filtering
    display_graph = graph.copy()
    
    # Filter edges by relation type if specified
    if filter_relations:
        edges_to_remove = []
        for u, v, data in display_graph.edges(data=True):
            if 'relation' in data and data['relation'] not in filter_relations:
                edges_to_remove.append((u, v))
        
        for edge in edges_to_remove:
            display_graph.remove_edge(*edge)
    
    # Remove isolated nodes (no connections)
    display_graph.remove_nodes_from(list(nx.isolates(display_graph)))
    
    # If graph is empty after filtering, show a message
    if len(display_graph.nodes) == 0:
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, "No nodes to display with current filter", 
                 horizontalalignment='center', fontsize=14)
        plt.axis('off')
        plt.show()
        return
    
    if interactive:
        # Use Pyvis for interactive visualization
        return _draw_interactive_graph(display_graph, layout_type)
    else:
        # Use Matplotlib for static visualization
        return _draw_static_graph(display_graph, layout_type, save_path)

def _draw_interactive_graph(graph, layout_type="hierarchical"):
    """
    Draw an interactive graph using Pyvis.
    
    Args:
        graph: NetworkX graph object
        layout_type: Type of layout ('hierarchical', 'circular', 'spring', 'kamada_kawai')
    """
    # Create a Pyvis network
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
    
    # Create a temporary HTML file
    fd, path = tempfile.mkstemp(suffix='.html')
    
    # Save and open the network visualization
    network.save_graph(path)
    webbrowser.open('file://' + path, new=2)
    
    print(f"Interactive graph opened in your web browser. You can drag nodes to reposition them.")
    print(f"Temporary file created at: {path}")
    
    return path

def _draw_static_graph(graph, layout_type="hierarchical", save_path=None):
    """
    Draw a static graph using Matplotlib.
    
    Args:
        graph: NetworkX graph object
        layout_type: Type of layout ('hierarchical', 'circular', 'spring', 'kamada_kawai')
        save_path: Path to save the image (None to display)
    """
    # Choose layout based on parameter
    if layout_type == "hierarchical":
        try:
            # Requires pygraphviz
            pos = graphviz_layout(graph, prog="dot")
        except:
            print("Pygraphviz not available, falling back to spring layout")
            # Use spring layout with more spacing
            pos = nx.spring_layout(graph, k=1.5, iterations=50, seed=42)
    elif layout_type == "circular":
        pos = nx.circular_layout(graph, scale=2.0)
    elif layout_type == "kamada_kawai":
        pos = nx.kamada_kawai_layout(graph, scale=2.0)
    else:  # Default to spring layout
        pos = nx.spring_layout(graph, k=1.5, iterations=50, seed=42)
    
    # Create figure with larger size
    plt.figure(figsize=(16, 12))
    
    # Define node colors and sizes based on type
    node_colors = []
    node_sizes = []
    for n in graph.nodes:
        ntype = graph.nodes[n].get("type", "")
        if ntype == "file":
            node_colors.append("#4287f5")  # Blue
            node_sizes.append(3000)
        elif ntype == "function":
            node_colors.append("#f5a742")  # Orange
            node_sizes.append(2000)
        else:
            node_colors.append("#aaaaaa")  # Gray
            node_sizes.append(1500)
    
    # Define edge colors based on relation type
    edge_colors = []
    for u, v, data in graph.edges(data=True):
        relation = data.get('relation', '')
        if relation == 'contains':
            edge_colors.append('#2ecc71')  # Green
        elif relation == 'imports':
            edge_colors.append('#e74c3c')  # Red
        elif relation == 'calls':
            edge_colors.append('#9b59b6')  # Purple
        else:
            edge_colors.append('#95a5a6')  # Gray
    
    # Draw nodes
    nx.draw_networkx_nodes(
        graph, 
        pos, 
        node_color=node_colors, 
        node_size=node_sizes,
        alpha=0.9,
        edgecolors='black',
        linewidths=1
    )
    
    # Draw edges with arrows
    nx.draw_networkx_edges(
        graph, 
        pos, 
        edge_color=edge_colors,
        width=1.5,
        alpha=0.7,
        arrowsize=15,
        arrowstyle='->',
        connectionstyle='arc3,rad=0.1'  # Curved edges to avoid overlap
    )
    
    # Draw labels with better font and positioning
    label_pos = {k: (v[0], v[1] + 0.1) for k, v in pos.items()}  # Adjust label positions
    nx.draw_networkx_labels(
        graph, 
        label_pos, 
        font_size=10,
        font_family='sans-serif',
        font_weight='bold',
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle='round,pad=0.3')
    )
    
    # Draw edge labels with better positioning
    edge_labels = nx.get_edge_attributes(graph, "relation")
    nx.draw_networkx_edge_labels(
        graph, 
        pos, 
        edge_labels=edge_labels,
        font_size=8,
        font_family='sans-serif',
        alpha=0.7,
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
    )
    
    # Create legend
    legend_elements = [
        mpatches.Patch(color='#4287f5', label='File'),
        mpatches.Patch(color='#f5a742', label='Function'),
        mpatches.Patch(color='#2ecc71', label='Contains'),
        mpatches.Patch(color='#e74c3c', label='Imports'),
        mpatches.Patch(color='#9b59b6', label='Calls')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    
    # Add title
    plt.title("Knowledge Graph of Codebase", fontsize=16, fontweight='bold')
    
    # Remove axes
    plt.axis('off')
    
    # Tight layout
    plt.tight_layout()
    
    # Save or show
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Graph saved to {save_path}")
    else:
        plt.show()