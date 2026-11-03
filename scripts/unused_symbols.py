import ast
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Set

class SymbolVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.private_functions: Set[str] = set()
        self.used_names: Set[str] = set()
        self.current_function: str = ""
        self.local_vars: Dict[str, Set[str]] = {}
        self.used_local_vars: Dict[str, Set[str]] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name.startswith('_') and not node.name.startswith('__'):
            if not self.current_function:
                self.private_functions.add(node.name)

        prev_function = self.current_function
        self.current_function = node.name
        if node.name not in self.local_vars:
            self.local_vars[node.name] = set()
        if node.name not in self.used_local_vars:
            self.used_local_vars[node.name] = set()

        self.generic_visit(node)
        self.current_function = prev_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit_FunctionDef(node) # type: ignore

    def visit_arg(self, node: ast.arg) -> None:
        if self.current_function:
            self.local_vars[self.current_function].add(node.arg)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            if self.current_function:
                self.local_vars[self.current_function].add(node.id)
        elif isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
            if self.current_function:
                self.used_local_vars[self.current_function].add(node.id)
        self.generic_visit(node)

def analyze_file(filepath: Path) -> List[str]:
    try:
        content = filepath.read_text(encoding='utf-8')
        tree = ast.parse(content, filename=str(filepath))
    except Exception as e:
        return [f"Error parsing {filepath}: {e}"]

    visitor = SymbolVisitor()
    visitor.visit(tree)

    unused = []
    for func in sorted(visitor.private_functions):
        if func not in visitor.used_names:
            unused.append(f"{filepath}: Unused private function '{func}'")

    for func, vars_set in sorted(visitor.local_vars.items()):
        used_vars = visitor.used_local_vars.get(func, set())
        for var in sorted(vars_set):
            if not var.startswith('_') and var not in used_vars:
                unused.append(f"{filepath}: Unused local variable '{var}' in function '{func}'")

    return unused

def main() -> int:
    parser = argparse.ArgumentParser(description="Find unused private functions and local variables.")
    parser.add_argument("files", nargs="+", type=Path, help="Files to analyze")
    args = parser.parse_args()

    all_unused = []
    for filepath in args.files:
        if filepath.is_file():
            all_unused.extend(analyze_file(filepath))

    for msg in all_unused:
        print(msg)

    return 1 if all_unused else 0

if __name__ == "__main__":
    sys.exit(main())
