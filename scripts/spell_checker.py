#!/usr/bin/env python3
"""Codebase spelling and typo auditor with built-in dictionary and typos-cli integration."""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

IGNORED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", "dist",
    "build", ".ai_checkpoints", ".cache", ".pytest_cache",
}

# Common developer spelling mistakes mapping incorrect -> correct
TYPO_DICTIONARY: dict[str, str] = {
    "recieve": "receive",
    "recieved": "received",
    "reciever": "receiver",
    "recieving": "receiving",
    "seperate": "separate",
    "seperated": "separated",
    "seperator": "separator",
    "seperately": "separately",
    "definately": "definitely",
    "definitly": "definitely",
    "occured": "occurred",
    "occurence": "occurrence",
    "occurance": "occurrence",
    "existance": "existence",
    "dependancy": "dependency",
    "dependancies": "dependencies",
    "refering": "referring",
    "refered": "referred",
    "successfull": "successful",
    "successfullly": "successfully",
    "unforseen": "unforeseen",
    "compatability": "compatibility",
    "paramater": "parameter",
    "paramaters": "parameters",
    "arguement": "argument",
    "arguements": "arguments",
    "neccessary": "necessary",
    "necesary": "necessary",
    "untill": "until",
    "wierd": "weird",
    "truely": "truly",
    "maintainance": "maintenance",
    "transfered": "transferred",
    "writting": "writing",
    "modifed": "modified",
    "initialze": "initialize",
    "initialzer": "initializer",
    "instanciate": "instantiate",
    "calback": "callback",
    "synchornize": "synchronize",
    "insteuctions": "instructions",
    "insteuction": "instruction",
    "evrry": "every",
    "evetything": "everything",
    "autoamtically": "automatically",
    "autoamtic": "automatic",
    "alreayd": "already",
    "ahrdcoded": "hardcoded",
    "implment": "implement",
    "implmentation": "implementation",
    "functon": "function",
    "funtion": "function",
    "variabel": "variable",
    "variabels": "variables",
}

WORD_SPLIT_RE = re.compile(r"[A-Za-z]+")


def split_identifier_words(token: str) -> list[str]:
    # Split camelCase and PascalCase
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)", token)
    return words if words else [token]


def check_line_spelling(line: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    tokens = WORD_SPLIT_RE.findall(line)
    for token in tokens:
        subwords = split_identifier_words(token)
        for w in subwords:
            low = w.lower()
            if low in TYPO_DICTIONARY:
                correct = TYPO_DICTIONARY[low]
                findings.append((w, correct))
    return findings


def audit_file_native(path: Path) -> list[tuple[int, str, str, str]]:
    findings: list[tuple[int, str, str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return findings

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("# noqa") or '": "' in line:
            continue
        hits = check_line_spelling(line)
        for wrong, right in hits:
            findings.append((i, wrong, right, line.strip()))
    return findings


def run_external_typos(target: Path) -> str | None:
    executable = shutil.which("typos") or shutil.which("typos.exe")
    cmd: list[str] = []
    if executable:
        cmd = [executable, str(target)]
    elif shutil.which("uv"):
        cmd = ["uv", "tool", "run", "typos", str(target)]
    elif shutil.which("uvx"):
        cmd = ["uvx", "typos", str(target)]

    if not cmd:
        return None

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return res.stdout or res.stderr
    except Exception:
        return None


def scan_target(target: Path, use_external: bool = True) -> dict[Path, list[tuple[int, str, str, str]]]:
    findings: dict[Path, list[tuple[int, str, str, str]]] = {}
    if target.is_file():
        hits = audit_file_native(target)
        if hits:
            findings[target] = hits
        return findings

    for p in target.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORED_DIRS for part in p.parts):
            continue
        if p.suffix not in {".py", ".md", ".txt", ".sh", ".bat", ".json", ".js", ".ts", ".html"}:
            continue
        hits = audit_file_native(p)
        if hits:
            findings[p] = hits
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit source code, comments, and docs for spelling errors.")
    parser.add_argument("target", nargs="?", default=".", help="Target file or directory")
    parser.add_argument("--native-only", action="store_true", help="Bypass external typos tool")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        sys.stderr.write(f"Error: Target path does not exist: {target_path}\n")
        sys.exit(1)

    if not args.native_only:
        ext_output = run_external_typos(target_path)
        if ext_output and ext_output.strip():
            print("=" * 70)
            print("                 Source Code Spelling Audit (typos-cli)")
            print("=" * 70)
            print(ext_output.strip())
            print("=" * 70)
            sys.exit(0)

    findings = scan_target(target_path)
    total_typos = sum(len(hits) for hits in findings.values())

    if not total_typos:
        print("[OK] Clean. No spelling errors or typos detected.")
        sys.exit(0)

    print("=" * 70)
    print(f"  [!] Found {total_typos} spelling mistake(s) or typo(s)")
    print("=" * 70)
    for path, hits in findings.items():
        try:
            rel = str(path.relative_to(target_path))
        except ValueError:
            rel = str(path)
        print(f"\n{rel}:")
        for lineno, wrong, right, snippet in hits:
            print(f"  Line {lineno:<4} '{wrong}' -> '{right}'")
    print("=" * 70)
    sys.exit(1)


if __name__ == "__main__":
    main()
