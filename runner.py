#!/usr/bin/env python3
import ast
import os
import sys
import argparse
from code_parser import CodeGraphBuilder
from visualize_graph import draw_graph
from db_manager import DatabaseManager

def add_parent_links(tree):
    """Add parent links to AST nodes for function call resolution."""
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate a knowledge graph of Python code.')
    parser.add_argument('directory', nargs='?', default='test-project',
                        help='Directory to parse (default: test-project)')
    
    # Visualization options
    vis_group = parser.add_argument_group('Visualization Options')
    vis_group.add_argument('--interactive', '-i', action='store_true',
                        help='Use interactive visualization (default)')
    vis_group.add_argument('--static', '-s', action='store_true',
                        help='Use static visualization')
    vis_group.add_argument('--layout', '-l', choices=['hierarchical', 'circular', 'spring', 'kamada_kawai'],
                        default='hierarchical', help='Layout type (default: hierarchical)')
    vis_group.add_argument('--filter', '-f', nargs='+', choices=['contains', 'imports', 'calls'],
                        help='Filter by relation types')
    vis_group.add_argument('--output', '-o', help='Save visualization to file')
    
    # Graph content options
    content_group = parser.add_argument_group('Graph Content Options')
    content_group.add_argument('--include-builtins', action='store_true',
                        help='Include built-in functions in the graph (default: excluded)')
    content_group.add_argument('--include-stdlib', action='store_true',
                        help='Include standard library functions in the graph (default: excluded)')
    
    # Database options
    db_group = parser.add_argument_group('Database Options')
    db_group.add_argument('--store-db', action='store_true',
                        help='Store graph data in MongoDB')
    db_group.add_argument('--project-name', default=None,
                        help='Project name for database storage')
    db_group.add_argument('--list-graphs', action='store_true',
                        help='List all stored graphs')
    # Vector database search options commented out
    # db_group.add_argument('--search-nodes', default=None,
    #                     help='Search for similar nodes')
    # db_group.add_argument('--search-edges', default=None,
    #                     help='Search for similar edges')
    # db_group.add_argument('--graph-id', default=None,
    #                     help='Graph ID for search operations')
    # db_group.add_argument('--top-k', type=int, default=5,
    #                     help='Number of search results to return')
    db_group.add_argument('--delete-graph', default=None,
                        help='Delete a graph by ID')
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Handle database-only operations
    if args.list_graphs or args.delete_graph:  # Removed search_nodes and search_edges
        db_manager = DatabaseManager()
        
        if args.list_graphs:
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
                print("No graphs found in the database.")
            
            db_manager.close()
            return
        
        if args.delete_graph:
            success = db_manager.delete_graph(args.delete_graph)
            if success:
                print(f"Graph {args.delete_graph} deleted successfully.")
            else:
                print(f"Failed to delete graph {args.delete_graph}.")
            
            db_manager.close()
            return
        
        # Vector database search functionality commented out
        # if args.search_nodes:
        #     results = db_manager.search_similar_nodes(
        #         args.search_nodes, 
        #         top_k=args.top_k, 
        #         graph_id=args.graph_id
        #     )
        #     
        #     if results:
        #         print(f"\nSearch results for nodes similar to '{args.search_nodes}':")
        #         for i, result in enumerate(results):
        #             print(f"{i+1}. {result['metadata']['name']} (Type: {result['metadata']['type']})")
        #             print(f"   Score: {result['score']:.4f}")
        #             print(f"   Graph ID: {result['metadata']['graph_id']}")
        #             print()
        #     else:
        #         print("No similar nodes found.")
        #     
        #     db_manager.close()
        #     return
        # 
        # if args.search_edges:
        #     results = db_manager.search_similar_edges(
        #         args.search_edges, 
        #         top_k=args.top_k, 
        #         graph_id=args.graph_id
        #     )
        #     
        #     if results:
        #         print(f"\nSearch results for edges similar to '{args.search_edges}':")
        #         for i, result in enumerate(results):
        #             print(f"{i+1}. {result['metadata']['source']} -> {result['metadata']['target']} (Relation: {result['metadata']['relation']})")
        #             print(f"   Score: {result['score']:.4f}")
        #             print(f"   Graph ID: {result['metadata']['graph_id']}")
        #             print()
        #     else:
        #         print("No similar edges found.")
        #     
        #     db_manager.close()
        #     return
    
    # Regular graph generation
    print(f"Parsing directory: {args.directory}")
    
    # Create the graph builder with options for excluding built-ins and stdlib
    builder = CodeGraphBuilder(
        args.directory,
        exclude_builtins=not args.include_builtins,
        exclude_stdlib=not args.include_stdlib
    )
    
    # Add parent links to AST nodes for function call resolution
    for dirpath, _, filenames in os.walk(args.directory):
        for file in filenames:
            if file.endswith(".py"):
                try:
                    with open(os.path.join(dirpath, file), "r", encoding="utf-8") as f:
                        source = f.read()
                    tree = ast.parse(source)
                    add_parent_links(tree)
                except Exception as e:
                    print(f"Error parsing {os.path.join(dirpath, file)}: {str(e)}")
    
    # Parse the project
    graph = builder.parse_project()
    
    # Store in database if requested
    if args.store_db:
        project_name = args.project_name or os.path.basename(os.path.abspath(args.directory))
        db_manager = DatabaseManager()
        graph_id = db_manager.store_graph(graph, project_name)
        print(f"Graph stored in MongoDB with ID: {graph_id}")
        db_manager.close()
    
    # Determine visualization type
    interactive = not args.static
    
    # Draw the graph
    print(f"Generating {'interactive' if interactive else 'static'} visualization with {args.layout} layout...")
    draw_graph(
        graph,
        interactive=interactive,
        layout_type=args.layout,
        filter_relations=args.filter,
        save_path=args.output
    )
    
    print("Done!")

if __name__ == "__main__":
    main()
