import ast
import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Any

class CoverageVisitor(ast.NodeVisitor):
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.functions_count = 0
        self.params_count = 0
        self.params_annotated = 0
        self.returns_count = 0
        self.returns_annotated = 0
        self.unannotated_funcs: List[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node)

    def _process_function(self, node: ast.AST) -> None:
        self.functions_count += 1
        name = getattr(node, "name", "<unknown>")

        has_missing = False

        args = node.args
        all_args = args.posonlyargs + args.args + args.kwonlyargs
        if args.vararg:
            all_args.append(args.vararg)
        if args.kwarg:
            all_args.append(args.kwarg)

        # Count parameters
        for arg in all_args:
            # Skip self/cls by convention for methods (though technically we should check context)
            if arg.arg in ('self', 'cls') and not arg.annotation:
                continue
            self.params_count += 1
            if arg.annotation is not None:
                self.params_annotated += 1
            else:
                has_missing = True

        # Count returns
        # Init methods don't technically need return annotation but it's strict here
        if name != "__init__":
            self.returns_count += 1
            if getattr(node, "returns", None) is not None:
                self.returns_annotated += 1
            else:
                has_missing = True

        if has_missing:
            self.unannotated_funcs.append(f"{self.filepath}:{getattr(node, 'lineno', 0)} {name}")

        self.generic_visit(node)

def analyze_file(filepath: str) -> CoverageVisitor:
    path = Path(filepath)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=filepath)
    visitor = CoverageVisitor(filepath)
    visitor.visit(tree)
    return visitor

def main(args: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Type Coverage Analyzer")
    parser.add_argument("target", nargs="?", default=".", help="Target directory or file")
    parsed_args = parser.parse_args(args)

    target_path = Path(parsed_args.target)
    files_to_check: List[Path] = []

    if target_path.is_file() and target_path.suffix == ".py":
        files_to_check.append(target_path)
    elif target_path.is_dir():
        files_to_check.extend(target_path.rglob("*.py"))

    total_funcs = 0
    total_params = 0
    total_params_ann = 0
    total_returns = 0
    total_returns_ann = 0
    all_unannotated: List[str] = []

    for f in files_to_check:
        try:
            visitor = analyze_file(str(f))
            total_funcs += visitor.functions_count
            total_params += visitor.params_count
            total_params_ann += visitor.params_annotated
            total_returns += visitor.returns_count
            total_returns_ann += visitor.returns_annotated
            all_unannotated.extend(visitor.unannotated_funcs)
        except Exception as e:
            print(f"Error analyzing {f}: {e}")

    print(f"Total functions: {total_funcs}")

    param_pct = (total_params_ann / total_params * 100) if total_params > 0 else 100.0
    print(f"Parameters: {total_params_ann}/{total_params} ({param_pct:.1f}%)")

    ret_pct = (total_returns_ann / total_returns * 100) if total_returns > 0 else 100.0
    print(f"Returns: {total_returns_ann}/{total_returns} ({ret_pct:.1f}%)")

    if all_unannotated:
        print("\nUnannotated functions:")
        for func in all_unannotated:
            print(f"  {func}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
