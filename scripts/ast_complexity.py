import ast
import argparse
import sys
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FunctionComplexity:
    name: str
    lineno: int
    complexity: int
    filepath: str


class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.functions: List[FunctionComplexity] = []
        self._current_complexity: int = 0
        self._in_function: bool = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node)

    def _process_function(self, node: ast.AST) -> None:
        prev_in_function = self._in_function
        prev_complexity = self._current_complexity

        self._in_function = True
        self._current_complexity = 1

        self.generic_visit(node)

        name = getattr(node, "name", "<unknown>")
        lineno = getattr(node, "lineno", 0)
        func_comp = FunctionComplexity(name, lineno, self._current_complexity, self.filepath)
        self.functions.append(func_comp)

        self._in_function = prev_in_function
        self._current_complexity = prev_complexity

    def _increment(self, amount: int = 1) -> None:
        if self._in_function:
            self._current_complexity += amount

    def visit_If(self, node: ast.If) -> None:
        self._increment()
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self._increment()
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._increment()
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._increment()
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self._increment()
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self._increment()
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self._increment()
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        self._increment()
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self._increment(len(node.values) - 1)
        self.generic_visit(node)


def compute_complexity(filepath: str, source_code: str) -> List[FunctionComplexity]:
    tree = ast.parse(source_code, filename=filepath)
    visitor = ComplexityVisitor(filepath)
    visitor.visit(tree)
    return visitor.functions


def analyze_files(filepaths: List[str]) -> List[FunctionComplexity]:
    results: List[FunctionComplexity] = []
    for filepath in filepaths:
        path = Path(filepath)
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8")
        results.extend(compute_complexity(filepath, source))
    return results


def main(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="AST Cyclomatic Complexity")
    parser.add_argument("files", nargs="+", help="Files to analyze")
    parser.add_argument("--max-complexity", type=int, default=10, help="Max complexity")
    parser.add_argument("--sort-by-complexity", action="store_true", help="Sort results")
    parsed_args = parser.parse_args(args)

    results = analyze_files(parsed_args.files)
    if parsed_args.sort_by_complexity:
        results.sort(key=lambda x: x.complexity, reverse=True)

    exit_code = 0
    for res in results:
        flag = "!" if res.complexity > parsed_args.max_complexity else " "
        print(f"[{flag}] {res.filepath}:{res.lineno} {res.name} - {res.complexity}")
        if res.complexity > parsed_args.max_complexity:
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
