# Code Knowledge Graph Visualizer

This project creates a visual knowledge graph of Python code relationships, showing files, functions, and their connections. It also provides database storage for graph data, allowing for persistent storage and semantic search capabilities.

## Features

- **Static Visualization**: Generate a one-time visualization of code relationships
- **Dynamic Visualization**: Watch for file changes and update the graph automatically
- **Live Web Visualization**: Interactive web-based visualization with real-time updates
- **Customizable Layouts**: Choose between different graph layouts
- **Interactive Controls**: Drag nodes, zoom, and filter relationships
- **Database Storage**: Store graph data in MongoDB (metadata) and vector database (embeddings)
- **Semantic Search**: Search for similar nodes and edges using natural language

## Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install them manually:

```bash
pip install networkx matplotlib watchdog pyvis pymongo sentence-transformers Qdrant-client python-dotenv
```

For the hierarchical layout, you'll also need:

```bash
pip install pygraphviz
```

Note: Installing pygraphviz may require additional system dependencies (graphviz).

### Database Requirements

- **MongoDB**: For storing graph metadata
  - Local installation or MongoDB Atlas cloud account
- **Qdrant**: For storing vector embeddings
  - Requires a Qdrant account and API key (free tier available)
- **Sentence Transformers**: For generating embeddings
  - Automatically installed with the requirements

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

Database Options:
  --store-db            Store graph data in MongoDB and vector database
  --project-name        Project name for database storage
  --list-graphs         List all stored graphs
  --search-nodes        Search for similar nodes
  --search-edges        Search for similar edges
  --graph-id            Graph ID for search operations
  --top-k               Number of search results to return
  --delete-graph        Delete a graph by ID
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

## Database Storage and Search

The project now supports storing graph data in MongoDB (for metadata) and a vector database (for embeddings). This enables persistent storage of graph data and semantic search capabilities.

### Setup

1. Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
```

2. Edit the `.env` file to include your MongoDB connection string and Qdrant API key:

```
# MongoDB connection
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=code_graph_db
MONGO_COLLECTION=graph_metadata

# Qdrant connection
Qdrant_API_KEY=your-Qdrant-api-key
Qdrant_ENVIRONMENT=us-west1-gcp
Qdrant_INDEX_NAME=code-graph-embeddings

# Embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Database Operations

#### Store a Graph

To store a graph in the databases:

```bash
python runner.py [directory] --store-db --project-name "My Project"
```

If `--project-name` is not provided, the directory name will be used.

#### List Stored Graphs

To list all stored graphs:

```bash
python runner.py --list-graphs
```

#### Search for Similar Nodes

To search for nodes similar to a text query:

```bash
python runner.py --search-nodes "file that handles authentication"
```

You can limit the search to a specific graph:

```bash
python runner.py --search-nodes "file that handles authentication" --graph-id <graph_id>
```

#### Search for Similar Edges

To search for edges (relationships) similar to a text query:

```bash
python runner.py --search-edges "function that calls database operations"
```

#### Delete a Graph

To delete a graph from the databases:

```bash
python runner.py --delete-graph <graph_id>
```

## Troubleshooting

- If the graph is too cluttered, try changing the layout or disabling physics
- For large codebases, the hierarchical layout often provides the clearest visualization
- If nodes overlap too much, you can manually drag them to better positions
- If there are too many built-in function calls cluttering the graph, use the default settings which exclude them
- Use the `--filter` option to show only specific types of relationships (e.g., `--filter contains calls` to show only file-function and function-function relationships)
- If you encounter database connection issues, check your `.env` file and ensure your MongoDB server is running
- For vector database operations, ensure you have a valid Qdrant API key
