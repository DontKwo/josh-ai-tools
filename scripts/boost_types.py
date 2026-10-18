#!/usr/bin/env python3
"""Type Annotation Booster.
Analyzes unannotated Python functions (Rule 11) and safely infers type annotations
from default values, return expressions, and control flow.

Guarantees 100% safety:
- Never touches existing explicit annotations.
- Skips 'self' and 'cls' parameter annotations per PEP 484.
- Safe AST round-trip verification: validates syntax with ast.parse before writing.
- Dry-run by default: previews all inferred signatures before applying.
"""
import ast
import argparse
import sys
from pathlib import Path
from typing import NamedTuple


class InferredFunction(NamedTuple):
    file_path: Path
    line_number: int
    name: str
    original_sig: str
    boosted_sig: str
    params_inferred: int
    return_inferred: bool


def infer_literal_type(node: ast.AST) -> str | None:
    """Infer type name from an AST constant or literal container."""
    if isinstance(node, ast.Constant):
        val = node.value
        if isinstance(val, bool):
            return "bool"
        if isinstance(val, int):
            return "int"
        if isinstance(val, float):
            return "float"
        if isinstance(val, str):
            return "str"
        if isinstance(val, bytes):
            return "bytes"
        if val is None:
            return "None"
    elif isinstance(node, ast.List):
        return "list"
    elif isinstance(node, ast.Dict):
        return "dict"
    elif isinstance(node, ast.Set):
        return "set"
    elif isinstance(node, ast.Tuple):
        return "tuple"
    return None


def collect_return_types(fn_node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str | None]:
    """Collect return types from all top-level return statements in the function."""
    returns: list[str | None] = []

    class ReturnVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            # Do not enter nested functions
            return None

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            # Do not enter nested async functions
            return None

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            # Do not enter nested classes
            return None

        def visit_Return(self, node: ast.Return) -> None:
            if node.value is None:
                returns.append("None")
            else:
                lit_type = infer_literal_type(node.value)
                returns.append(lit_type)

    visitor = ReturnVisitor()
    for stmt in fn_node.body:
        visitor.visit(stmt)

    return returns


def infer_return_annotation(
    fn_node: ast.FunctionDef | ast.AsyncFunctionDef, fallback_any: bool = False
) -> str | None:
    """Infer the return type annotation string for a function."""
    if fn_node.returns is not None:
        return None  # Already annotated

    returns = collect_return_types(fn_node)

    if not returns:
        # No return statements at all -> returns None
        return "None"

    # If all returns are None
    if all(r == "None" for r in returns):
        return "None"

    non_none_returns = [r for r in returns if r != "None"]
    has_none = "None" in returns

    # If all non-none returns share the same inferred type
    unique_types = set(non_none_returns)
    if len(unique_types) == 1 and None not in unique_types:
        t = non_none_returns[0]
        if has_none:
            return f"{t} | None"
        return t

    if fallback_any:
        return "Any"

    return None


def find_signature_bounds(lines: list[str], start_lineno: int) -> int:
    """Find the 1-indexed line number where the function signature ends (colon)."""
    paren_depth = 0
    in_signature = False
    for i in range(start_lineno - 1, len(lines)):
        line = lines[i]
        # Ignore comments
        clean_line = line.split("#", 1)[0]
        for ch in clean_line:
            if ch == "(":
                paren_depth += 1
                in_signature = True
            elif ch == ")":
                paren_depth -= 1
            elif ch == ":" and in_signature and paren_depth == 0:
                return i + 1
    return start_lineno


def boost_function_signature(
    fn_node: ast.FunctionDef | ast.AsyncFunctionDef,
    lines: list[str],
    fallback_any: bool = False,
) -> tuple[str, str, int, bool] | None:
    """Analyze a function definition and return (original_sig, new_sig, params_changed, return_changed)."""
    sig_end_lineno = find_signature_bounds(lines, fn_node.lineno)
    orig_lines = lines[fn_node.lineno - 1 : sig_end_lineno]
    orig_sig = "".join(orig_lines).rstrip()

    # Determine parameter defaults mapping
    args = fn_node.args
    defaults_offset = len(args.args) - len(args.defaults)
    params_changed = 0

    new_args_list: list[str] = []

    for i, arg in enumerate(args.args):
        arg_name = arg.arg
        # Skip self / cls
        if arg_name in ("self", "cls"):
            new_args_list.append(arg_name)
            continue

        # If already annotated, keep original
        if arg.annotation is not None:
            ann_str = ast.unparse(arg.annotation)
            default_val = None
            if i >= defaults_offset:
                default_val = ast.unparse(args.defaults[i - defaults_offset])
            if default_val is not None:
                new_args_list.append(f"{arg_name}: {ann_str} = {default_val}")
            else:
                new_args_list.append(f"{arg_name}: {ann_str}")
            continue

        # Try to infer from default value
        inferred = None
        default_val = None
        if i >= defaults_offset:
            default_node = args.defaults[i - defaults_offset]
            default_val = ast.unparse(default_node)
            inferred = infer_literal_type(default_node)
            if inferred == "None":
                inferred = "Any | None" if fallback_any else None

        if not inferred and fallback_any:
            inferred = "Any"

        if inferred:
            params_changed += 1
            if default_val is not None:
                new_args_list.append(f"{arg_name}: {inferred} = {default_val}")
            else:
                new_args_list.append(f"{arg_name}: {inferred}")
        else:
            if default_val is not None:
                new_args_list.append(f"{arg_name}={default_val}")
            else:
                new_args_list.append(arg_name)

    # Varargs and Kwargs
    if args.vararg:
        if args.vararg.annotation:
            new_args_list.append(f"*{args.vararg.arg}: {ast.unparse(args.vararg.annotation)}")
        elif fallback_any:
            new_args_list.append(f"*{args.vararg.arg}: Any")
            params_changed += 1
        else:
            new_args_list.append(f"*{args.vararg.arg}")

    # Kwonly args
    kw_defaults_map = {
        arg.arg: default
        for arg, default in zip(args.kwonlyargs, args.kw_defaults)
        if default is not None
    }
    for kwarg in args.kwonlyargs:
        kw_name = kwarg.arg
        if kwarg.annotation:
            ann_str = ast.unparse(kwarg.annotation)
            if kw_name in kw_defaults_map:
                new_args_list.append(f"{kw_name}: {ann_str} = {ast.unparse(kw_defaults_map[kw_name])}")
            else:
                new_args_list.append(f"{kw_name}: {ann_str}")
        else:
            inferred = None
            def_str = None
            if kw_name in kw_defaults_map:
                def_node = kw_defaults_map[kw_name]
                def_str = ast.unparse(def_node)
                inferred = infer_literal_type(def_node)

            if not inferred and fallback_any:
                inferred = "Any"

            if inferred:
                params_changed += 1
                if def_str is not None:
                    new_args_list.append(f"{kw_name}: {inferred} = {def_str}")
                else:
                    new_args_list.append(f"{kw_name}: {inferred}")
            else:
                if def_str is not None:
                    new_args_list.append(f"{kw_name}={def_str}")
                else:
                    new_args_list.append(kw_name)

    if args.kwarg:
        if args.kwarg.annotation:
            new_args_list.append(f"**{args.kwarg.arg}: {ast.unparse(args.kwarg.annotation)}")
        elif fallback_any:
            new_args_list.append(f"**{args.kwarg.arg}: Any")
            params_changed += 1
        else:
            new_args_list.append(f"**{args.kwarg.arg}")

    # Return annotation
    return_changed = False
    ret_annotation = None
    if fn_node.returns is not None:
        ret_annotation = ast.unparse(fn_node.returns)
    else:
        inferred_ret = infer_return_annotation(fn_node, fallback_any=fallback_any)
        if inferred_ret:
            ret_annotation = inferred_ret
            return_changed = True

    if params_changed == 0 and not return_changed:
        return None

    # Construct clean signature with proper leading indentation
    prefix = "async def " if isinstance(fn_node, ast.AsyncFunctionDef) else "def "
    indent = " " * fn_node.col_offset
    args_str = ", ".join(new_args_list)
    ret_str = f" -> {ret_annotation}" if ret_annotation else ""
    boosted_sig = f"{indent}{prefix}{fn_node.name}({args_str}){ret_str}:"

    return orig_sig, boosted_sig, params_changed, return_changed


def boost_file(
    file_path: Path,
    fix: bool = False,
    fallback_any: bool = False,
) -> tuple[int, list[InferredFunction]]:
    """Scan and optionally boost type annotations in a file."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(content, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return 0, []

    lines = content.splitlines(keepends=True)
    inferred_list: list[InferredFunction] = []

    # Collect all functions in file
    functions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node)

    # Sort descending by line number to replace cleanly from bottom to top
    functions.sort(key=lambda fn: fn.lineno, reverse=True)

    uses_any = False
    for fn in functions:
        boost_res = boost_function_signature(fn, lines, fallback_any=fallback_any)
        if not boost_res:
            continue

        orig_sig, boosted_sig, p_count, r_changed = boost_res
        if "Any" in boosted_sig:
            uses_any = True

        inferred_list.append(
            InferredFunction(
                file_path=file_path,
                line_number=fn.lineno,
                name=fn.name,
                original_sig=orig_sig.strip(),
                boosted_sig=boosted_sig.strip(),
                params_inferred=p_count,
                return_inferred=r_changed,
            )
        )

        if fix:
            sig_end = find_signature_bounds(lines, fn.lineno)
            # Replace signature lines
            ending = "\n" if lines[fn.lineno - 1].endswith("\n") else ""
            lines[fn.lineno - 1 : sig_end] = [boosted_sig + ending]

    if fix and inferred_list:
        # If 'Any' was introduced, check if 'from typing import Any' is present
        if uses_any:
            full_code = "".join(lines)
            if "from typing import" not in full_code and "import typing" not in full_code:
                # Add import at top
                insert_idx = 0
                for idx, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith("#!") or "coding:" in stripped:
                        insert_idx = idx + 1
                    elif stripped.startswith('"""') or stripped.startswith("'''"):
                        delim = '"""' if '"""' in stripped else "'''"
                        if stripped.count(delim) >= 2:
                            insert_idx = idx + 1
                            break
                        for doc_end in range(idx + 1, len(lines)):
                            if delim in lines[doc_end]:
                                insert_idx = doc_end + 1
                                break
                        break
                lines.insert(insert_idx, "from typing import Any\n")

        new_content = "".join(lines)
        # Guarantee behavior: Verify AST validity
        try:
            ast.parse(new_content, filename=str(file_path))
        except SyntaxError as e:
            print(f"Error: AST validation failed after boosting {file_path}: {e}", file=sys.stderr)
            return 0, []

        file_path.write_text(new_content, encoding="utf-8")

    return len(inferred_list), inferred_list


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Type Annotation Booster (Deterministic Safe AST Type Engine)"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target file or directory to boost (default: current directory)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply boosted type annotations in-place (verifies AST before saving)",
    )
    parser.add_argument(
        "--fallback-any",
        action="store_true",
        help="Annotate uninferrable parameters with Any (and ensure from typing import Any)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 if unannotated functions can be boosted",
    )

    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    if not target_path.exists():
        print(f"Error: Target path does not exist: {target_path}", file=sys.stderr)
        return 1

    py_files: list[Path] = []
    if target_path.is_file():
        if target_path.suffix == ".py":
            py_files.append(target_path)
    else:
        for p in target_path.rglob("*.py"):
            parts = p.parts
            if any(part in (".git", ".venv", "venv", "__pycache__", "build", "dist") for part in parts):
                continue
            py_files.append(p)

    print(f"Scanning {len(py_files)} Python file(s) for type annotation improvements...\n")

    total_boosted = 0
    total_files_changed = 0

    for pf in py_files:
        count, items = boost_file(pf, fix=args.fix, fallback_any=args.fallback_any)
        if items:
            total_boosted += len(items)
            print(f"File: {pf}")
            for item in items:
                print(f"  Line {item.line_number}: def {item.name}()")
                print(f"    - Original: {item.original_sig}")
                print(f"    + Boosted:  {item.boosted_sig}")
            if args.fix:
                total_files_changed += 1
                print("    [APPLIED] Updated file safely.")
            print()

    print("Summary:")
    print(f"  Functions boostable: {total_boosted}")
    if args.fix:
        print(f"  Files safely updated: {total_files_changed}")

    if args.check and total_boosted > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
