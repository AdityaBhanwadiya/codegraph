from code_parser import CodeGraphBuilder
from visualize_graph import _draw_interactive_graph
import json

# Path to the project
directory_path = "/Users/harshladani/Desktop/ML/codegraph/test-project"

# Create the graph builder
builder = CodeGraphBuilder(directory_path)

# Parse the project
graph = builder.parse_project()

# Generate HTML visualization
html_path = _draw_interactive_graph(graph, layout_type="hierarchical")

# Print result
result = {
    "status": "success",
    "message": f"Interactive visualization saved to {html_path}",
    "node_count": len(graph.nodes),
    "edge_count": len(graph.edges)
}
print(json.dumps(result, indent=2))
