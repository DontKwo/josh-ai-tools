#!/usr/bin/env python3
"""Standard Model Context Protocol (MCP) Server for Josh's AI Tools.
Exposes the 45-rule linter, safe auto-fixer, symbol map generator, and encoding cleaner
directly as native MCP tools to Claude, Cursor, Windsurf, Cline, and Antigravity.
"""

import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINTER_SCRIPT = REPO_ROOT / "scripts" / "claudemd_linter.py"
FIXER_SCRIPT = REPO_ROOT / "scripts" / "lint_fixer.py"
REPO_MAP_SCRIPT = REPO_ROOT / "scripts" / "repo_map.py"
ENCODING_SCRIPT = REPO_ROOT / "scripts" / "clean_encoding.py"
DOCTOR_SCRIPT = REPO_ROOT / "scripts" / "doctor.py"
PRUNE_SCRIPT = REPO_ROOT / "scripts" / "prune_dead_code.py"
BOOST_SCRIPT = REPO_ROOT / "scripts" / "boost_types.py"
DEPS_SCRIPT = REPO_ROOT / "scripts" / "check_dependencies.py"
MARKDOWN_SCRIPT = REPO_ROOT / "scripts" / "to_markdown.py"
TREE_SCRIPT = REPO_ROOT / "scripts" / "dir_overview.py"
SEARCH_SCRIPT = REPO_ROOT / "scripts" / "fast_search.py"
SLICE_SCRIPT = REPO_ROOT / "scripts" / "slice_file.py"
DIFF_SCRIPT = REPO_ROOT / "scripts" / "redact_diff.py"
ROLLBACK_SCRIPT = REPO_ROOT / "scripts" / "rollback.py"
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync_rules.py"
TEST_RUNNER_SCRIPT = REPO_ROOT / "scripts" / "smart_test_runner.py"
TOKEN_BUDGET_SCRIPT = REPO_ROOT / "scripts" / "token_budget.py"
PACK_CONTEXT_SCRIPT = REPO_ROOT / "scripts" / "pack_context.py"
SECRET_SCRIPT = REPO_ROOT / "scripts" / "secret_sanitizer.py"
HOOK_SCRIPT = REPO_ROOT / "scripts" / "install_antigravity_hooks.py"
VARS_SCRIPT = REPO_ROOT / "scripts" / "check_variable_names.py"
SPELL_SCRIPT = REPO_ROOT / "scripts" / "spell_checker.py"
GRILL_SCRIPT = REPO_ROOT / "scripts" / "grill_user.py"

IS_WINDOWS = platform.system() == "Windows"
BASE_CMD: list[str] = (
    ["uv", "run", "--no-project", "python"]
    if shutil.which("uv")
    else [sys.executable or ("python" if IS_WINDOWS else "python3")]
)


def send_response(response: dict) -> None:
    body = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(body.encode('utf-8'))}\r\n\r\n{body}")
    sys.stdout.flush()


def run_command_tool(cmd: list[str], cwd: Path | None = None) -> str:
    try:
        res = subprocess.run(
            cmd,
            cwd=str(cwd or REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        output = res.stdout
        if res.stderr:
            output += ("\n" if output else "") + res.stderr
        return output or "Executed successfully with no output."
    except Exception as e:
        return f"Error executing tool: {e}"


def resolve_cwd(arguments: dict, target_key: str = "target") -> Path | None:
    if "cwd" in arguments and arguments["cwd"]:
        return Path(arguments["cwd"]).resolve()
    target = arguments.get(target_key)
    if target:
        tp = Path(target)
        if tp.is_dir():
            return tp.resolve()
        if tp.is_file():
            return tp.parent.resolve()
    return None


TOOLS = [
    {
        "name": "run_linter",
        "description": "Run the 45-rule claudemd linter against code/markdown files to detect AI writing fluff, syntax, and GUI flaws.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target file or directory path (default: current directory)"},
                "diff_only": {"type": "boolean", "description": "Only lint modified/untracked git files"},
                "no_cache": {"type": "boolean", "description": "Bypass incremental caching and force full re-scan"},
            },
        },
    },
    {
        "name": "run_safe_fixer",
        "description": "Apply guaranteed, 100% deterministic safe fixes for mechanical rules (== None -> is None, curly quotes, non-breaking spaces). NEVER touches em dashes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target file or directory to fix"},
                "dry_run": {"type": "boolean", "description": "Preview fixes without modifying files"},
                "fix_emojis": {"type": "boolean", "description": "Safely strip unicode emojis"},
            },
            "required": ["target"],
        },
    },
    {
        "name": "get_symbol_map",
        "description": "Generate an ultra-compact, token-efficient architectural map of classes, methods, and functions across a codebase.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Root path of repository or directory"},
                "max_lines": {"type": "integer", "description": "Maximum lines in output (default: 300)"},
            },
        },
    },
    {
        "name": "clean_mojibake",
        "description": "Scan and clean corrupted character encodings, double-encoded UTF-8/Windows-1252 sequences, and broken placeholders.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "File or folder to clean"},
                "dry_run": {"type": "boolean", "description": "Preview changes without writing"},
                "degrees_to_word": {"type": "boolean", "description": "Replace '°' with 'degrees'"},
            },
        },
    },
    {
        "name": "check_environment_health",
        "description": "Run diagnostic check on AI tool configurations, Python version, dependencies, and verify path health.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "heal": {"type": "boolean", "description": "Automatically heal broken or stale linter paths"},
            },
        },
    },
    {
        "name": "prune_dead_code",
        "description": "Safely detect and prune unused imports (zombie imports) and detect dead functions/classes via AST analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target file or directory to scan"},
                "fix": {"type": "boolean", "description": "Safely remove unused imports in-place"},
            },
        },
    },
    {
        "name": "boost_type_annotations",
        "description": "Infer and apply type annotations to unannotated functions based on default values and return types (Rule 11).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target file or directory to boost"},
                "fix": {"type": "boolean", "description": "Apply inferred type annotations in-place"},
                "fallback_any": {"type": "boolean", "description": "Annotate uninferrable parameters with Any"},
            },
        },
    },
    {
        "name": "scan_hallucinated_dependencies",
        "description": "Scan codebase for AI-hallucinated imports, undeclared packages, and unused dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target file or directory to scan"},
                "strict": {"type": "boolean", "description": "Fail on undeclared dependencies"},
            },
        },
    },
    {
        "name": "convert_to_markdown",
        "description": "Convert PDF, DOCX, PPTX, XLSX, CSV, IPYNB, or HTML to structured, token-efficient Markdown.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Path to document file to convert"},
                "max_pages": {"type": "integer", "description": "Maximum pages/slides/sheets to parse"},
                "max_lines": {"type": "integer", "description": "Maximum output lines to emit"},
                "meta": {"type": "boolean", "description": "Prepend document metadata frontmatter"},
            },
            "required": ["target"],
        },
    },
    {
        "name": "get_codebase_tree",
        "description": "Generate a clean, token-efficient directory tree with file sizes and line counts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Root directory path"},
                "depth": {"type": "integer", "description": "Maximum tree depth (default: 3)"},
                "ext": {"type": "string", "description": "Filter by comma-separated extensions (e.g. py,ts)"},
                "stats": {"type": "boolean", "description": "Include line counts and file sizes"},
            },
        },
    },
    {
        "name": "search_codebase",
        "description": "Fast regex and symbol search across text files with context lines and token caps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Regex or literal search string"},
                "target": {"type": "string", "description": "Target directory or file"},
                "context": {"type": "integer", "description": "Context lines around match (default: 1)"},
                "ext": {"type": "string", "description": "Filter extensions (e.g. py,md)"},
                "max_results": {"type": "integer", "description": "Maximum matches to return (default: 30)"},
                "ignore_case": {"type": "boolean", "description": "Case-insensitive search"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "slice_file_lines",
        "description": "Read exact line ranges, head, or tail of files with line numbers for token efficiency.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Path to file"},
                "range": {"type": "string", "description": "Line range (e.g. 50-100)"},
                "head": {"type": "integer", "description": "First N lines"},
                "tail": {"type": "integer", "description": "Last N lines"},
            },
            "required": ["target"],
        },
    },
    {
        "name": "redact_git_diff",
        "description": "Compress git diff outputs for LLM prompts by focusing on AST-level changes (60-80% token savings).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "staged": {"type": "boolean", "description": "Diff staged changes"},
                "commit": {"type": "string", "description": "Diff against specific commit (e.g. HEAD~1)"},
                "max_lines": {"type": "integer", "description": "Maximum diff lines to return (default: 300)"},
                "stat": {"type": "boolean", "description": "Include compression statistics"},
            },
        },
    },
    {
        "name": "manage_checkpoints",
        "description": "Save instant workspace snapshots, preview diffs, and rollback code edits if AI makes broken changes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["save", "restore", "diff", "list", "clear"],
                    "description": "Checkpoint operation to perform",
                },
                "name": {"type": "string", "description": "Checkpoint name (optional)"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "sync_rules",
        "description": "Synchronize development and linting rules across all configured AI tools.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Specific rule file path to copy from"},
                "dry_run": {"type": "boolean", "description": "Preview sync without writing"},
            },
        },
    },
    {
        "name": "smart_test_runner",
        "description": "Run unit tests impacted by modified Python files using AST dependency analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "files": {"type": "array", "items": {"type": "string"}, "description": "Specific files or tests to check"},
                "all": {"type": "boolean", "description": "Run all tests unconditionally"},
                "runner": {"type": "string", "enum": ["unittest", "pytest"], "description": "Test runner"},
            },
        },
    },
    {
        "name": "analyze_token_budget",
        "description": "Calculate token usage and context budget across files and directories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target file or directory (default: current directory)"},
                "threshold": {"type": "integer", "description": "Token threshold to flag large files (default: 5000)"},
            },
        },
    },
    {
        "name": "pack_context_bundle",
        "description": "Bundle codebase context, diffs, and symbol maps into token-efficient LLM payloads.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "files": {"type": "array", "items": {"type": "string"}, "description": "Files to include in bundle"},
                "diff": {"type": "boolean", "description": "Include git diff"},
                "staged": {"type": "boolean", "description": "Include staged git diff"},
                "symbols": {"type": "boolean", "description": "Include codebase symbol map"},
            },
        },
    },
    {
        "name": "scan_secrets",
        "description": "Scan and mask API keys, tokens, and credentials before AI prompt transmission.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target file or directory"},
                "mask": {"type": "boolean", "description": "Return file content with credentials masked"},
            },
        },
    },
    {
        "name": "install_completion_hooks",
        "description": "Configure Antigravity completion hook to trigger linter when tasks finish.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scope": {"type": "string", "enum": ["workspace", "global", "both"], "description": "Target scope"},
                "event": {"type": "string", "enum": ["PostInvocation", "Stop"], "description": "Completion event"},
                "remove": {"type": "boolean", "description": "Uninstall the hook"},
            },
        },
    },
    {
        "name": "audit_variable_names",
        "description": "Audit Python codebase for short, cryptic, or non-descriptive variable and parameter names.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target file or directory (default: current directory)"},
            },
        },
    },
    {
        "name": "check_spelling",
        "description": "Check codebase source files, comments, and documentation for spelling errors and typos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target file or directory (default: current directory)"},
            },
        },
    },
    {
        "name": "grill_user",
        "description": "Grill the user relentlessly about a plan, decision, or idea to stress-test their thinking.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic, plan, decision, or idea to grill the user about."},
            },
        },
    },
]


def _handle_run_linter(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [str(LINTER_SCRIPT), target]
    if arguments.get("diff_only"):
        cmd.append("--diff")
    if arguments.get("no_cache"):
        cmd.append("--no-cache")
    output = run_command_tool(cmd, cwd=effective_cwd)
    # Inspect project-specific report
    target_path = Path(target)
    project_root = (effective_cwd / target_path).resolve()
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", project_root.name) or "project"
    report_file = REPO_ROOT / "scripts" / f"lint_report_{safe_name}.txt"
    if not report_file.exists():
        report_file = REPO_ROOT / "scripts" / "lint_report.txt"
    if report_file.exists():
        try:
            report_content = report_file.read_text(encoding="utf-8")
            output = f"{output}\n\n--- LINT REPORT ---\n{report_content}"
        except OSError:
            return [{"type": "text", "text": output}]
    return [{"type": "text", "text": output}]


def _handle_run_safe_fixer(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(FIXER_SCRIPT), target]
    if arguments.get("dry_run", False):
        cmd.append("--dry-run")
    if arguments.get("fix_emojis", False):
        cmd.append("--fix-emojis")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_get_symbol_map(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    max_lines = str(arguments.get("max_lines", 300))
    cmd = BASE_CMD + [ str(REPO_MAP_SCRIPT), target, "--max-lines", max_lines]
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_clean_mojibake(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(ENCODING_SCRIPT), target]
    if arguments.get("dry_run", False):
        cmd.append("--dry-run")
    if arguments.get("degrees_to_word", False):
        cmd.append("--degrees-to-word")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_check_environment_health(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    cmd = BASE_CMD + [ str(DOCTOR_SCRIPT)]
    if arguments.get("heal", False):
        cmd.append("--heal")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_prune_dead_code(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(PRUNE_SCRIPT), target]
    if arguments.get("fix", False):
        cmd.append("--fix")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_boost_type_annotations(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(BOOST_SCRIPT), target]
    if arguments.get("fix", False):
        cmd.append("--fix")
    if arguments.get("fallback_any", False):
        cmd.append("--fallback-any")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_scan_hallucinated_dependencies(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(DEPS_SCRIPT), target]
    if arguments.get("strict", False):
        cmd.append("--strict")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_convert_to_markdown(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments["target"]
    cmd = BASE_CMD + [ str(MARKDOWN_SCRIPT), target]
    if "max_pages" in arguments:
        cmd.extend(["--max-pages", str(arguments["max_pages"])])
    if "max_lines" in arguments:
        cmd.extend(["--max-lines", str(arguments["max_lines"])])
    if arguments.get("meta"):
        cmd.append("--meta")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_get_codebase_tree(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(TREE_SCRIPT), target]
    if "depth" in arguments:
        cmd.extend(["--depth", str(arguments["depth"])])
    if "ext" in arguments:
        cmd.extend(["--ext", str(arguments["ext"])])
    if arguments.get("stats"):
        cmd.append("--stats")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_search_codebase(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    query = arguments["query"]
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(SEARCH_SCRIPT), query, target]
    if "context" in arguments:
        cmd.extend(["--context", str(arguments["context"])])
    if "ext" in arguments:
        cmd.extend(["--ext", str(arguments["ext"])])
    if "max_results" in arguments:
        cmd.extend(["--max-results", str(arguments["max_results"])])
    if arguments.get("ignore_case"):
        cmd.append("--ignore-case")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_slice_file_lines(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments["target"]
    cmd = BASE_CMD + [ str(SLICE_SCRIPT), target]
    if "range" in arguments:
        cmd.append(str(arguments["range"]))
    if "head" in arguments:
        cmd.extend(["--head", str(arguments["head"])])
    if "tail" in arguments:
        cmd.extend(["--tail", str(arguments["tail"])])
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_redact_git_diff(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    cmd = BASE_CMD + [ str(DIFF_SCRIPT)]
    if arguments.get("staged"):
        cmd.append("--staged")
    if "commit" in arguments:
        cmd.extend(["--commit", str(arguments["commit"])])
    if "max_lines" in arguments:
        cmd.extend(["--max-lines", str(arguments["max_lines"])])
    if arguments.get("stat"):
        cmd.append("--stat")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_manage_checkpoints(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    action = arguments["action"]
    cmd = BASE_CMD + [ str(ROLLBACK_SCRIPT), action]
    if "name" in arguments and arguments["name"]:
        cmd.append(str(arguments["name"]))
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_sync_rules(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    cmd = BASE_CMD + [ str(SYNC_SCRIPT)]
    if "source" in arguments:
        cmd.extend(["--source", str(arguments["source"])])
    if arguments.get("dry_run"):
        cmd.append("--dry-run")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_smart_test_runner(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    cmd = BASE_CMD + [ str(TEST_RUNNER_SCRIPT)]
    if arguments.get("all"):
        cmd.append("--all")
    if "runner" in arguments:
        cmd.extend(["--runner", str(arguments["runner"])])
    if "files" in arguments and isinstance(arguments["files"], list):
        cmd.extend([str(f) for f in arguments["files"]])
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_analyze_token_budget(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(TOKEN_BUDGET_SCRIPT), target]
    if "threshold" in arguments:
        cmd.extend(["--threshold", str(arguments["threshold"])])
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_pack_context_bundle(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    cmd = BASE_CMD + [ str(PACK_CONTEXT_SCRIPT)]
    if arguments.get("diff"):
        cmd.append("--diff")
    if arguments.get("staged"):
        cmd.append("--staged")
    if arguments.get("symbols"):
        cmd.append("--symbols")
    if "files" in arguments and isinstance(arguments["files"], list):
        cmd.extend([str(f) for f in arguments["files"]])
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_scan_secrets(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(SECRET_SCRIPT), target]
    if arguments.get("mask"):
        cmd.append("--mask")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_install_completion_hooks(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    cmd = BASE_CMD + [ str(HOOK_SCRIPT)]
    if "scope" in arguments:
        cmd.extend(["--scope", str(arguments["scope"])])
    if "event" in arguments:
        cmd.extend(["--event", str(arguments["event"])])
    if arguments.get("remove"):
        cmd.append("--remove")
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_audit_variable_names(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(VARS_SCRIPT), target]
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_check_spelling(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    target = arguments.get("target", ".")
    cmd = BASE_CMD + [ str(SPELL_SCRIPT), target]
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


def _handle_grill_user(arguments: dict, effective_cwd: Path | None) -> list[dict]:
    topic = arguments.get("topic", "")
    cmd = BASE_CMD + [str(GRILL_SCRIPT), topic]
    output = run_command_tool(cmd, cwd=effective_cwd)
    return [{"type": "text", "text": output}]


TOOL_HANDLERS = {
    "run_linter": _handle_run_linter,
    "run_safe_fixer": _handle_run_safe_fixer,
    "get_symbol_map": _handle_get_symbol_map,
    "clean_mojibake": _handle_clean_mojibake,
    "check_environment_health": _handle_check_environment_health,
    "prune_dead_code": _handle_prune_dead_code,
    "boost_type_annotations": _handle_boost_type_annotations,
    "scan_hallucinated_dependencies": _handle_scan_hallucinated_dependencies,
    "convert_to_markdown": _handle_convert_to_markdown,
    "get_codebase_tree": _handle_get_codebase_tree,
    "search_codebase": _handle_search_codebase,
    "slice_file_lines": _handle_slice_file_lines,
    "redact_git_diff": _handle_redact_git_diff,
    "manage_checkpoints": _handle_manage_checkpoints,
    "sync_rules": _handle_sync_rules,
    "smart_test_runner": _handle_smart_test_runner,
    "analyze_token_budget": _handle_analyze_token_budget,
    "pack_context_bundle": _handle_pack_context_bundle,
    "scan_secrets": _handle_scan_secrets,
    "install_completion_hooks": _handle_install_completion_hooks,
    "audit_variable_names": _handle_audit_variable_names,
    "check_spelling": _handle_check_spelling,
    "grill_user": _handle_grill_user,
}


def handle_tool_call(name: str, arguments: dict) -> list[dict]:
    effective_cwd = resolve_cwd(arguments)
    handler = TOOL_HANDLERS.get(name)
    if handler:
        return handler(arguments, effective_cwd)
    return [{"type": "text", "text": f"Error: Unknown tool '{name}'"}]


def main() -> None:
    buffer = ""
    while True:
        line = sys.stdin.readline()
        if not line:
            break

        # Read JSON-RPC line or header
        if line.lower().startswith("content-length:"):
            length = int(line.split(":")[1].strip())
            # Skip empty lines until body
            while True:
                blank = sys.stdin.readline()
                if blank in ("\r\n", "\n", ""):
                    break
            raw_body = sys.stdin.read(length)
            msg = json.loads(raw_body)
        else:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                msg = json.loads(line_str)
            except Exception:
                continue

        method = msg.get("method")
        msg_id = msg.get("id")

        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "josh-ai-tools-mcp", "version": "1.0.0"},
                },
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS},
            })
        elif method == "tools/call":
            params = msg.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})
            result = handle_tool_call(name, arguments)
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"content": result},
            })
        elif msg_id is not None:
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            })


if __name__ == "__main__":
    main()

