import sys
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def parse_line(line: str) -> Tuple[str, str, str]:
    """Extract key, value, and type annotation from a line."""
    if not line or line.strip().startswith("#") or "=" not in line:
        return "", "", ""
    key, remainder = line.split("=", 1)
    key = key.strip()
    type_ann = ""
    match = re.search(r"#\s*type:\s*(int|url|bool)", remainder, re.IGNORECASE)
    if match:
        type_ann = match.group(1).lower()

    value = remainder
    if " #" in value:
        value = value.split(" #", 1)[0]
    value = value.strip()
    return key, value, type_ann

def parse_file(filepath: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Parse an env file returning keys, values, and types."""
    data: Dict[str, str] = {}
    types: Dict[str, str] = {}
    if not filepath.exists():
        return data, types
    with filepath.open("r", encoding="utf-8") as file_handle:
        for line in file_handle:
            key, value, t_ann = parse_line(line.strip())
            if key:
                data[key] = value
                if t_ann:
                    types[key] = t_ann
    return data, types

def validate_type(val: str, t_ann: str) -> bool:
    """Check if a value matches the requested type."""
    if t_ann == "int":
        try:
            int(val)
            return True
        except ValueError:
            return False
    if t_ann == "bool":
        return val.lower() in ("true", "false", "1", "0", "yes", "no")
    if t_ann == "url":
        return val.startswith("http://") or val.startswith("https://")
    return True

def validate_env(env_path: Path, example_path: Path) -> List[str]:
    """Validate .env against .env.example."""
    errors: List[str] = []
    if not example_path.exists():
        errors.append(f"Missing {example_path}")
        return errors

    env_data, _ = parse_file(env_path)
    ex_data, ex_types = parse_file(example_path)

    for key in ex_data:
        if key not in env_data:
            errors.append(f"Missing required key: {key}")
        else:
            value = env_data[key]
            if not value:
                errors.append(f"Empty value for key: {key}")
            elif key in ex_types and not validate_type(value, ex_types[key]):
                errors.append(f"Invalid type for {key}: expected {ex_types[key]}")

    for key in env_data:
        if key not in ex_data:
            errors.append(f"Unexpected key: {key}")

    return errors

def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for env validator."""
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default=".env")
    parser.add_argument("--example", default=".env.example")
    parsed = parser.parse_args(args)

    errors = validate_env(Path(parsed.env), Path(parsed.example))
    if errors:
        for err in errors:
            print(err)
        return 1
    print("OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
