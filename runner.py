#!/usr/bin/env python3
import ast
import os
import sys
import argparse
from code_parser import CodeGraphBuilder
from visualize_graph import draw_graph

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
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
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
