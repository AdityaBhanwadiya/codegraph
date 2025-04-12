# Code Knowledge Graph Visualizer

This project creates a visual knowledge graph of Python code relationships, showing files, functions, and their connections.

## Features

- **Static Visualization**: Generate a one-time visualization of code relationships
- **Dynamic Visualization**: Watch for file changes and update the graph automatically
- **Live Web Visualization**: Interactive web-based visualization with real-time updates
- **Customizable Layouts**: Choose between different graph layouts
- **Interactive Controls**: Drag nodes, zoom, and filter relationships

## Requirements

Install the required dependencies:

```bash
pip install networkx matplotlib watchdog pyvis
```

For the hierarchical layout, you'll also need:

```bash
pip install pygraphviz
```

Note: Installing pygraphviz may require additional system dependencies (graphviz).

## Usage

### Static Visualization

To generate a one-time visualization of your code:

```bash
python runner.py [directory]
```

By default, built-in functions and standard library functions are excluded from the graph to reduce clutter. You can include them with these options:

```bash
python runner.py --include-builtins --include-stdlib
```

#### Command Line Options

```
positional arguments:
  directory             Directory to parse (default: test-project)

Visualization Options:
  --interactive, -i     Use interactive visualization (default)
  --static, -s          Use static visualization
  --layout {hierarchical,circular,spring,kamada_kawai}, -l {hierarchical,circular,spring,kamada_kawai}
                        Layout type (default: hierarchical)
  --filter {contains,imports,calls} [{contains,imports,calls} ...], -f {contains,imports,calls} [{contains,imports,calls} ...]
                        Filter by relation types
  --output OUTPUT, -o OUTPUT
                        Save visualization to file

Graph Content Options:
  --include-builtins    Include built-in functions in the graph (default: excluded)
  --include-stdlib      Include standard library functions in the graph (default: excluded)
```

### Dynamic Visualization

To watch for file changes and update the graph automatically:

```bash
python dynamic_graph.py [project_directory]
```

If no directory is specified, it defaults to "test-project".

### Live Web Visualization (Recommended)

For the best experience with real-time updates and interactive controls:

```bash
python live_graph_server.py [project_directory]
```

This starts a web server and opens a browser with the interactive visualization. The graph updates automatically when files change.

## Interactive Controls

In the live web visualization:

- **Drag nodes**: Reposition nodes by dragging them
- **Zoom**: Use mouse wheel or pinch gestures to zoom
- **Reset View**: Click the "Reset View" button to fit all nodes
- **Toggle Physics**: Turn physics simulation on/off
- **Change Layout**: Select different layouts from the dropdown

## Understanding the Graph

The graph uses colors to represent different types of nodes and relationships:

- **Blue nodes**: Files
- **Orange nodes**: Functions
- **Green edges**: "Contains" relationship (file contains function)
- **Red edges**: "Imports" relationship (file imports another file)
- **Purple edges**: "Calls" relationship (function calls another function)

## Troubleshooting

- If the graph is too cluttered, try changing the layout or disabling physics
- For large codebases, the hierarchical layout often provides the clearest visualization
- If nodes overlap too much, you can manually drag them to better positions
- If there are too many built-in function calls cluttering the graph, use the default settings which exclude them
- Use the `--filter` option to show only specific types of relationships (e.g., `--filter contains calls` to show only file-function and function-function relationships)
