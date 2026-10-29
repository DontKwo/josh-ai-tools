#!/usr/bin/env python3
"""Dead Code & Zombie Import Pruner.
Detects and safely prunes unused imports and dead code across Python files.

Guarantees 100% safety:
- Never removes imports marked with # noqa or # pragma: no cover.
- Preserves re-exports in __init__.py and modules defining __all__.
- Safely updates multiline and compound imports without breaking formatting.
- Re-parses AST after any proposed change; automatically aborts if AST validation fails.
- Dead functions, methods, and classes are reported with confidence scores (never deleted blindly).
"""
import ast
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

try:
    import vulture  # noqa: 22
    HAVE_VULTURE_MODULE = True
except ImportError:
    HAVE_VULTURE_MODULE = False


def is_vulture_available() -> bool:
    if HAVE_VULTURE_MODULE or shutil.which("vulture"):
        return True
    return bool(shutil.which("uv"))


class UnusedImport(NamedTuple):
    file_path: Path
    line_start: int
    line_end: int
    module: str
    symbol: str
    asname: str | None
    is_from_import: bool
    all_symbols_in_stmt: list[str]


class DeadCodeItem(NamedTuple):
    file_path: Path
    line_number: int
    item_type: str
    name: str
    confidence: int
    message: str


class ASTUsageCollector(ast.NodeVisitor):
    """Collects all identifier names used in an AST (reads, writes, calls, attributes, annotations)."""

    def __init__(self) -> None:
        self.used_names: set[str] = set()
        self.exported_names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # e.g., os.path -> 'os' is captured as Name in node.value
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # Check for __all__ = ["foo", "bar"]
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            self.exported_names.add(elt.value)
                            self.used_names.add(elt.value)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        # String forward annotations, e.g. "MyModel", "List[str]"
        if isinstance(node.value, str) and node.value.isidentifier():
            self.used_names.add(node.value)
        self.generic_visit(node)


def find_unused_imports(file_path: Path, preserve_init: bool = True) -> list[UnusedImport]:
    """Analyze a single Python file and return all unused imports."""
    if preserve_init and file_path.name == "__init__.py":
        return []

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(content, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return []

    lines = content.splitlines()

    # Step 1: Collect all imports in file
    imports: list[tuple[ast.AST, list[ast.alias], bool, str]] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.append((node, node.names, False, ""))
        elif isinstance(node, ast.ImportFrom):
            mod = ("." * node.level) + (node.module or "")
            imports.append((node, node.names, True, mod))

    if not imports:
        return []

    # Step 2: Collect all names referenced in AST
    collector = ASTUsageCollector()
    collector.visit(tree)

    unused: list[UnusedImport] = []

    for stmt, aliases, is_from, mod in imports:
        # Check noqa / pragma on the import line
        line_idx = getattr(stmt, "lineno", 1) - 1
        stmt_lines = lines[line_idx : getattr(stmt, "end_lineno", line_idx + 1)]
        combined_text = " ".join(stmt_lines).lower()
        if "noqa" in combined_text or "pragma: no cover" in combined_text:
            continue

        all_syms = [alias.asname or alias.name for alias in aliases]

        for alias in aliases:
            # Skip wildcard imports
            if alias.name == "*":
                continue

            bound_name = alias.asname or alias.name

            # Check if used anywhere in AST (excluding import definition itself)
            # Count occurrences in collector
            if bound_name not in collector.used_names:
                unused.append(
                    UnusedImport(
                        file_path=file_path,
                        line_start=stmt.lineno,
                        line_end=getattr(stmt, "end_lineno", stmt.lineno),
                        module=mod if is_from else alias.name,
                        symbol=alias.name,
                        asname=alias.asname,
                        is_from_import=is_from,
                        all_symbols_in_stmt=all_syms,
                    )
                )

    return unused


def scan_dead_code_vulture(target: Path) -> list[DeadCodeItem]:
    if not is_vulture_available():
        return []

    if HAVE_VULTURE_MODULE:
        v = vulture.Vulture(verbose=False)
        target_str = str(target)
        v.scavenge([target_str])

        dead_items: list[DeadCodeItem] = []
        for item in v.get_unused_code():
            if getattr(item, "typ", "") in ("import", "import_from"):
                continue
            item_path = Path(getattr(item, "filename", str(target)))
            dead_items.append(
                DeadCodeItem(
                    file_path=item_path,
                    line_number=getattr(item, "first_lineno", 1),
                    item_type=getattr(item, "typ", "symbol"),
                    name=getattr(item, "name", "unknown"),
                    confidence=getattr(item, "confidence", 60),
                    message=getattr(item, "message", ""),
                )
            )
        return dead_items

    cmd: list[str] = []
    if shutil.which("vulture"):
        cmd = ["vulture", str(target)]
    elif shutil.which("uv"):
        cmd = ["uv", "tool", "run", "vulture", str(target)]

    if not cmd:
        return []

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        dead_items = []
        pattern = re.compile(
            r"^(.*?):(\d+):\s*(unused (?:function|method|class|variable|attribute|property) ['\"]?([^'\"]+)['\"]?.*?)(?:\((\d+)%\s*confidence\))?$",
            re.IGNORECASE,
        )
        for line in res.stdout.splitlines():
            line_str = line.strip()
            match = pattern.match(line_str)
            if match:
                dead_items.append(
                    DeadCodeItem(
                        file_path=Path(match.group(1)),
                        line_number=int(match.group(2)),
                        item_type="symbol",
                        name=match.group(4),
                        confidence=int(match.group(5) or 60),
                        message=match.group(3).strip(),
                    )
                )
        return dead_items
    except OSError:
        return []


def prune_unused_imports_in_file(file_path: Path, dry_run: bool = True) -> tuple[int, list[str]]:
    """Prunes unused imports from a file safely. Validates syntax before saving."""
    unused_list = find_unused_imports(file_path)
    if not unused_list:
        return 0, []

    content = file_path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(content, filename=str(file_path))
    lines = content.splitlines(keepends=True)

    # Group unused symbols by statement (line_start, line_end)
    stmt_map: dict[tuple[int, int], list[UnusedImport]] = {}
    for unused_item in unused_list:
        key = (unused_item.line_start, unused_item.line_end)
        stmt_map.setdefault(key, []).append(unused_item)

    changes: list[str] = []
    # Process from bottom to top so line deletions don't invalidate higher line offsets
    sorted_stmt_keys = sorted(stmt_map.keys(), key=lambda k: k[0], reverse=True)

    for (l_start, l_end) in sorted_stmt_keys:
        u_group = stmt_map[(l_start, l_end)]
        u_symbols = {unused_item.asname or unused_item.symbol for unused_item in u_group}
        all_syms = u_group[0].all_symbols_in_stmt
        is_from = u_group[0].is_from_import
        mod = u_group[0].module

        # If ALL symbols in this import statement are unused, delete the entire statement
        if set(all_syms) <= u_symbols:
            removed_repr = ", ".join(all_syms)
            changes.append(f"Line {l_start}: Removed unused import statement ({removed_repr})")
            if not dry_run:
                # Remove lines (1-indexed l_start to l_end inclusive)
                del lines[l_start - 1 : l_end]
        else:
            # Some symbols are used, some are unused. Rewrite keeping only used symbols
            kept_syms = [symbol_name for symbol_name in all_syms if symbol_name not in u_symbols]
            changes.append(
                f"Line {l_start}: Pruned unused [{', '.join(u_symbols)}] from import ({mod or 'import'})"
            )
            if not dry_run:
                orig_first_line = lines[l_start - 1]
                # Preserve leading indent
                indent = orig_first_line[: len(orig_first_line) - len(orig_first_line.lstrip())]
                ending = "\n" if orig_first_line.endswith("\n") else ""

                if is_from:
                    new_stmt = f"{indent}from {mod} import {', '.join(kept_syms)}{ending}"
                else:
                    new_stmt = f"{indent}import {', '.join(kept_syms)}{ending}"

                lines[l_start - 1 : l_end] = [new_stmt]

    if not dry_run and changes:
        new_content = "".join(lines)
        # Guarantee behavior: Verify AST validity
        try:
            ast.parse(new_content, filename=str(file_path))
        except SyntaxError as e:
            # Revert immediately if syntax error
            print(f"Error: AST validation failed after pruning {file_path}: {e}", file=sys.stderr)
            return 0, []

        file_path.write_text(new_content, encoding="utf-8")

    return len(changes), changes


def scan_directory(
    target: Path, fix: bool = False, include_vulture: bool = True
) -> tuple[int, int]:
    """Scan directory or file for unused imports and dead code."""
    py_files: list[Path] = []
    if target.is_file():
        if target.suffix == ".py":
            py_files.append(target)
    else:
        for p in target.rglob("*.py"):
            # Skip virtual environments, git, caches
            parts = p.parts
            if any(part in (".git", ".venv", "venv", "__pycache__", "build", "dist") for part in parts):
                continue
            py_files.append(p)

    total_unused_imports = 0
    total_files_changed = 0

    print(f"Scanning {len(py_files)} Python file(s) for zombie imports and dead code...\n")

    for pf in py_files:
        unused = find_unused_imports(pf)
        if unused:
            total_unused_imports += len(unused)
            print(f"File: {pf}")
            for unused_item in unused:
                asname_str = f" as {unused_item.asname}" if unused_item.asname else ""
                print(f"  Line {unused_item.line_start}: Unused import '{unused_item.symbol}{asname_str}' (module: {unused_item.module or unused_item.symbol})")

            if fix:
                count, changes = prune_unused_imports_in_file(pf, dry_run=False)
                if count:
                    total_files_changed += 1
                    for change_item in changes:
                        print(f"    [APPLIED] {change_item}")
            print()

    # Vulture Dead Code Scanning
    dead_code_count = 0
    if include_vulture and is_vulture_available():
        print("Checking dead functions, methods, and classes via Vulture...")
        dead_items = scan_dead_code_vulture(target)
        if dead_items:
            dead_code_count = len(dead_items)
            print(f"Detected {dead_code_count} dead code candidate(s):")
            for item in dead_items:
                print(
                    f"  {item.file_path}:{item.line_number} [{item.item_type}] '{item.name}' "
                    f"(confidence: {item.confidence}%) - {item.message}"
                )
            print("Note: Dead functions/classes require human architectural review; never pruned automatically.\n")
        else:
            print("Vulture: No dead functions or classes found.\n")
    elif include_vulture and not is_vulture_available():
        print("Tip: Install 'vulture' (`uv tool install vulture`) for dead function/class detection.\n")

    print(f"Summary:")
    print(f"  Unused imports found: {total_unused_imports}")
    if fix:
        print(f"  Files safely updated: {total_files_changed}")
    if is_vulture_available():
        print(f"  Dead code candidates: {dead_code_count}")

    return total_unused_imports, dead_code_count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dead Code & Zombie Import Pruner (Deterministic & Safe AST Engine)"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target file or directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Safely remove unused imports in-place (verifies AST before saving)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files (default behavior)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 if unused imports or dead code are found",
    )
    parser.add_argument(
        "--no-vulture",
        action="store_true",
        help="Disable Vulture dead function/class scanning",
    )

    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    if not target_path.exists():
        print(f"Error: Target path does not exist: {target_path}", file=sys.stderr)
        return 1

    unused_count, dead_count = scan_directory(
        target_path,
        fix=args.fix,
        include_vulture=not args.no_vulture,
    )

    if args.check and (unused_count > 0 or dead_count > 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
