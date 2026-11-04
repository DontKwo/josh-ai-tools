import argparse
import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set


def get_module_name(file_path: Path, root_path: Path) -> str:
    """Convert file path to module name relative to root."""
    rel_path: Path = file_path.relative_to(root_path)
    parts: List[str] = list(rel_path.parts)
    if parts and parts[-1] == "__init__.py":
        parts.pop()
    elif parts:
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


def parse_imports(file_path: Path, root_path: Path) -> List[str]:
    """Parse imports from a Python file using AST."""
    imports: List[str] = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content: str = file.read()
        tree: ast.AST = ast.parse(content, filename=str(file_path))
    except Exception:
        return imports

    rel_path: Path = file_path.relative_to(root_path)
    parts: List[str] = list(rel_path.parts)
    is_init: bool = parts[-1] == "__init__.py" if parts else False
    if is_init:
        parts.pop()
    elif parts:
        parts[-1] = parts[-1][:-3]

    package_parts: List[str] = parts if is_init else parts[:-1]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            level: int = node.level if node.level is not None else 0
            if level > 0:
                if level - 1 <= len(package_parts):
                    base_parts: List[str] = package_parts[:-(level-1)] if level - 1 > 0 else package_parts
                    base: str = ".".join(base_parts)
                    if node.module:
                        for alias in node.names:
                            imports.append(f"{base}.{node.module}.{alias.name}" if base else f"{node.module}.{alias.name}")
                        imports.append(f"{base}.{node.module}" if base else node.module)
                    else:
                        for alias in node.names:
                            imports.append(f"{base}.{alias.name}" if base else alias.name)
            else:
                if node.module:
                    for alias in node.names:
                        imports.append(f"{node.module}.{alias.name}")
                    imports.append(node.module)
    return imports


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in a directory tree."""
    python_files: List[Path] = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)
    return python_files


def build_dependency_graph(root_path: Path) -> Dict[str, List[str]]:
    """Build a graph of module dependencies."""
    graph: Dict[str, List[str]] = {}
    python_files: List[Path] = find_python_files(root_path)

    for file_path in python_files:
        module_name: str = get_module_name(file_path, root_path)
        imports: List[str] = parse_imports(file_path, root_path)
        graph[module_name] = imports

    return graph


def detect_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    """Detect cycles in the dependency graph using Tarjan's algorithm."""
    index: int = 0
    indices: Dict[str, int] = {}
    lowlinks: Dict[str, int] = {}
    stack: List[str] = []
    on_stack: Set[str] = set()
    cycles: List[List[str]] = []

    def strongconnect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in indices:
                strongconnect(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbor])

        if lowlinks[node] == indices[node]:
            scc: List[str] = []
            while True:
                w: str = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == node:
                    break
            if len(scc) > 1:
                cycles.append(scc)

    for node in graph:
        if node not in indices:
            strongconnect(node)

    return cycles


def output_dot_graph(graph: Dict[str, List[str]], out_path: Path) -> None:
    """Output the dependency graph in DOT format."""
    with open(out_path, "w", encoding="utf-8") as file:
        file.write("digraph G {\n")
        for node, neighbors in graph.items():
            for neighbor in neighbors:
                if neighbor in graph:
                    file.write(f'  "{node}" -> "{neighbor}";\n')
        file.write("}\n")


def main() -> int:
    """Main execution function."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description="Import Graph")
    parser.add_argument("directory", type=str, help="Directory to analyze")
    parser.add_argument("--dot", type=str, help="Output DOT graph to path", default="")

    args: argparse.Namespace = parser.parse_args()
    target_dir: Path = Path(args.directory).resolve()

    if not target_dir.is_dir():
        print(f"Error: {target_dir} is not a directory.")
        return 1

    graph: Dict[str, List[str]] = build_dependency_graph(target_dir)
    cycles: List[List[str]] = detect_cycles(graph)

    if cycles:
        print("Detected circular imports:")
        for cycle in cycles:
            print(f" - {' -> '.join(cycle)}")
    else:
        print("No circular imports detected.")

    if args.dot:
        dot_path: Path = Path(args.dot)
        output_dot_graph(graph, dot_path)
        print(f"DOT graph written to {dot_path}")

    return 0 if not cycles else 2


if __name__ == "__main__":
    sys.exit(main())
