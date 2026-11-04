import argparse
import sys
from pathlib import Path
from typing import List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def extract_rows(table_lines: List[str]) -> List[List[str]]:
    # Extracts cells from markdown table strings
    rows: List[List[str]] = []
    for line in table_lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        cells = [cell.strip() for cell in line.split("|")]
        rows.append(cells)
    return rows

def determine_alignment(delimiter_row: List[str]) -> List[str]:
    # Determines cell alignment based on colons
    alignments: List[str] = []
    for cell in delimiter_row:
        cell = cell.strip()
        left = cell.startswith(":")
        right = cell.endswith(":")
        if left and right:
            alignments.append("center")
        elif right:
            alignments.append("right")
        else:
            alignments.append("left")
    return alignments

def format_cell(cell: str, width: int, alignment: str) -> str:
    # Pads cell text according to alignment
    if alignment == "center":
        return cell.center(width)
    if alignment == "right":
        return cell.rjust(width)
    return cell.ljust(width)

def format_table(lines: List[str]) -> List[str]:
    # Formats the given lines of a single table
    if len(lines) < 2:
        return lines

    rows = extract_rows(lines)
    if len(rows) < 2:
        return lines

    alignments = determine_alignment(rows[1])
    num_cols = max(len(row) for row in rows)
    widths = [0] * num_cols
    for r_idx, row in enumerate(rows):
        for i, cell in enumerate(row):
            if i < num_cols:
                if r_idx != 1:
                    widths[i] = max(widths[i], len(cell))

    for i in range(num_cols):
        widths[i] = max(widths[i], 3)

    formatted_lines: List[str] = []
    for r_idx, row in enumerate(rows):
        padded_row = row + [""] * (num_cols - len(row))
        if r_idx == 1:
            delim_cells: List[str] = []
            for i, align in enumerate(alignments):
                if i >= num_cols:
                    break
                w = widths[i]
                if align == "center":
                    delim_cells.append(":" + "-" * (w - 2) + ":")
                elif align == "right":
                    delim_cells.append("-" * (w - 1) + ":")
                else:
                    delim_cells.append("-" * w)
            while len(delim_cells) < num_cols:
                delim_cells.append("-" * widths[len(delim_cells)])
            formatted_lines.append("| " + " | ".join(delim_cells) + " |")
        else:
            cells: List[str] = []
            for i in range(num_cols):
                align = alignments[i] if i < len(alignments) else "left"
                cells.append(format_cell(padded_row[i], widths[i], align))
            formatted_lines.append("| " + " | ".join(cells) + " |")

    return formatted_lines

def process_content(content: str) -> str:
    # Formats all markdown tables in the content text
    lines = content.splitlines(keepends=True)
    out_lines: List[str] = []

    in_code_block = False
    in_table = False
    table_lines: List[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            if in_table:
                formatted = format_table(table_lines)
                for f_line in formatted:
                    out_lines.append(f_line + "\n")
                table_lines = []
                in_table = False
            out_lines.append(line)
            continue

        if in_code_block:
            out_lines.append(line)
            continue

        if stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 1:
            if not in_table:
                in_table = True
            table_lines.append(line.rstrip("\n\r"))
        else:
            if in_table:
                formatted = format_table(table_lines)
                for f_line in formatted:
                    out_lines.append(f_line + "\n")
                table_lines = []
                in_table = False
            out_lines.append(line)

    if in_table:
        formatted = format_table(table_lines)
        for f_line in formatted:
            out_lines.append(f_line + "\n")

    return "".join(out_lines)

def process_file(target_file: Path, check_only: bool) -> bool:
    # Processes a file, formatting tables or just checking
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception:
        return True

    formatted = process_content(content)

    if content == formatted:
        return True

    if check_only:
        print(f"File unformatted: {target_file}")
        return False

    target_file.write_text(formatted, encoding="utf-8")
    print(f"Formatted: {target_file}")
    return True

def main(args: Optional[List[str]] = None) -> int:
    # Main entrypoint
    parser = argparse.ArgumentParser(description="Format markdown tables")
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")

    parsed = parser.parse_args(args)
    if not parsed.files:
        return 0

    all_ok = True
    for target_file in parsed.files:
        if target_file.is_file():
            is_ok = process_file(target_file, parsed.check)
            if not is_ok:
                all_ok = False

    if parsed.check and not all_ok:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
