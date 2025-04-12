import ast
import os
import builtins
import sys
import inspect
import networkx as nx

class CodeGraphBuilder:
    def __init__(self, root_dir, exclude_builtins=True, exclude_stdlib=True):
        self.root_dir = root_dir
        self.graph = nx.DiGraph()
        self.exclude_builtins = exclude_builtins
        self.exclude_stdlib = exclude_stdlib
        
        # Create a set of built-in function names
        self.builtin_functions = set(dir(builtins))
        
        # Add common Python types that are often called
        self.builtin_functions.update([
            'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'len', 'print', 'range', 'enumerate', 'zip', 'map', 'filter',
            'sum', 'min', 'max', 'sorted', 'reversed', 'any', 'all',
            'open', 'isinstance', 'hasattr', 'getattr', 'setattr', 'delattr',
            'super', 'property', 'staticmethod', 'classmethod'
        ])
        
        # Standard library modules to exclude
        self.stdlib_modules = set(sys.builtin_module_names)
        self.stdlib_modules.update([
            'os', 'sys', 're', 'math', 'random', 'datetime', 'time',
            'json', 'csv', 'collections', 'itertools', 'functools',
            'pathlib', 'shutil', 'tempfile', 'urllib', 'http', 'socket',
            'threading', 'multiprocessing', 'subprocess', 'logging'
        ])

    def parse_project(self):
        for dirpath, _, filenames in os.walk(self.root_dir):
            for file in filenames:
                if file.endswith(".py"):
                    filepath = os.path.join(dirpath, file)
                    self._parse_file(filepath)
        return self.graph

    def _parse_file(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
        
        # Add parent links to the AST
        self._add_parent_links(tree)

        file_node = os.path.basename(filepath)
        self.graph.add_node(file_node, type="file")

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.graph.add_node(node.name, type="function")
                self.graph.add_edge(file_node, node.name, relation="contains")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_file = node.module + ".py"
                    self.graph.add_node(imported_file, type="file")
                    self.graph.add_edge(file_node, imported_file, relation="imports")

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    
                    # Skip built-in functions if exclude_builtins is True
                    if self.exclude_builtins and func_name in self.builtin_functions:
                        continue
                    
                    # Add the function node
                    self.graph.add_node(func_name, type="function")
                    
                    # Add the edge from the caller to the function
                    caller = self._get_enclosing_function_name(node)
                    if caller:
                        self.graph.add_edge(caller, func_name, relation="calls")


    def _get_enclosing_function_name(self, node):
        while node:
            if isinstance(node, ast.FunctionDef):
                return node.name
            node = getattr(node, 'parent', None)
        return None
        
    def _add_parent_links(self, tree):
        """Add parent links to all nodes in the AST."""
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
                
    def _is_stdlib_module(self, module_name):
        """Check if a module is part of the standard library."""
        if module_name in self.stdlib_modules:
            return True
        
        # Check if the module is in the standard library paths
        for path in sys.path:
            if path.startswith(sys.prefix) and not 'site-packages' in path:
                if os.path.exists(os.path.join(path, module_name + '.py')):
                    return True
                if os.path.exists(os.path.join(path, module_name, '__init__.py')):
                    return True
        
        return False