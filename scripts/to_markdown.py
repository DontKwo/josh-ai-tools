#!/usr/bin/env python3
"""Universal File-to-Markdown Converter for AI Tooling.
Extracts structured Markdown from PDF, DOCX, PPTX, XLSX, CSV, IPYNB, HTML, and JSON
without requiring AI agents to invent ad-hoc parsing commands or waste tokens.

Guarantees 100% safety & zero required external dependencies:
- Pure Python stdlib parsers for DOCX, PPTX, XLSX, CSV, IPYNB, HTML, XML, and JSON.
- Native zipfile + XML parsing for Office Open XML formats (DOCX/PPTX/XLSX).
- Robust PDF extraction with pypdf/pdfplumber if available, and pure-Python stream fallback.
- Token-efficient formatting with page/slide limits, line caps, and table alignment.
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import zipfile
import zlib
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

# Configure stdout for clean UTF-8 across all platforms
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# =====================================================================
# PDF Extraction
# =====================================================================
def extract_pdf_pypdf(pdf_path: Path, max_pages: int | None = None) -> list[str]:
    """Extract text from PDF using pypdf or pdfplumber if installed."""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        pages_text: list[str] = []
        limit = min(len(reader.pages), max_pages) if max_pages else len(reader.pages)
        for i in range(limit):
            t = reader.pages[i].extract_text() or ""
            pages_text.append(t.strip())
        return pages_text
    except Exception:
        pass

    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            pages_text = []
            limit = min(len(pdf.pages), max_pages) if max_pages else len(pdf.pages)
            for i in range(limit):
                t = pdf.pages[i].extract_text() or ""
                pages_text.append(t.strip())
            return pages_text
    except Exception:
        pass

    return []


def extract_pdf_fallback(pdf_path: Path, max_pages: int | None = None) -> list[str]:
    """Pure Python stdlib fallback PDF text stream extractor."""
    try:
        data = pdf_path.read_bytes()
    except Exception as e:
        return [f"[Error reading PDF: {e}]"]

    pages_text: list[str] = []
    # Find all /FlateDecode streams
    stream_pattern = re.compile(b"stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
    streams = stream_pattern.findall(data)

    decompressed_chunks: list[str] = []
    for s in streams:
        try:
            decomp = zlib.decompress(s)
            # Extract text within parentheses in PDF text operators (TJ, Tj)
            text_matches = re.findall(rb"\((.*?)\)\s*T[jJ]", decomp)
            if text_matches:
                chunk = " ".join(
                    m.decode("latin1", errors="replace").replace("\\(", "(").replace("\\)", ")")
                    for m in text_matches
                )
                if chunk.strip():
                    decompressed_chunks.append(chunk.strip())
        except Exception:
            continue

    if decompressed_chunks:
        # Group chunks into synthetic pages
        per_page = max(1, len(decompressed_chunks) // 4)
        for i in range(0, len(decompressed_chunks), per_page):
            pages_text.append("\n\n".join(decompressed_chunks[i : i + per_page]))
            if max_pages and len(pages_text) >= max_pages:
                break
    else:
        # Raw regex search for printable text strings
        strings = re.findall(rb"\(([A-Za-z0-9 .,:;!?/'\"()\-+=_]{3,})\)", data)
        if strings:
            joined = " ".join(s.decode("latin1", errors="replace") for s in strings[:1000])
            pages_text.append(joined)
        else:
            pages_text.append("[PDF contains scanned images or encrypted text without readable fonts. Consider installing 'pypdf': pip install pypdf]")

    return pages_text


def convert_pdf_to_md(pdf_path: Path, max_pages: int | None = None) -> str:
    pages = extract_pdf_pypdf(pdf_path, max_pages=max_pages)
    if not pages:
        pages = extract_pdf_fallback(pdf_path, max_pages=max_pages)

    md_lines: list[str] = [f"# {pdf_path.stem} (PDF)\n"]
    for i, page_text in enumerate(pages, 1):
        md_lines.append(f"## Page {i}\n")
        md_lines.append(page_text if page_text else "_[Empty page]_")
        md_lines.append("\n")

    return "\n".join(md_lines)


# =====================================================================
# Word Document (.docx) Extraction (100% Stdlib OpenXML)
# =====================================================================
def convert_docx_to_md(docx_path: Path) -> str:
    try:
        with zipfile.ZipFile(docx_path, "r") as z:
            doc_xml = z.read("word/document.xml")
    except Exception as e:
        return f"# Error reading DOCX {docx_path.name}: {e}\n"

    tree = ET.fromstring(doc_xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    md_lines: list[str] = [f"# {docx_path.stem}\n"]

    for elem in tree.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        if tag == "p":
            p_style = elem.find(".//w:pStyle", ns)
            style_val = p_style.attrib.get(f"{{{ns['w']}}}val", "") if p_style is not None else ""

            # Collect text runs
            runs = elem.findall(".//w:r", ns)
            p_text = ""
            for r in runs:
                t_elem = r.find("w:t", ns)
                if t_elem is not None and t_elem.text:
                    text_frag = t_elem.text
                    is_bold = r.find("w:b", ns) is not None
                    is_italic = r.find("w:i", ns) is not None
                    if is_bold and is_italic:
                        text_frag = f"***{text_frag}***"
                    elif is_bold:
                        text_frag = f"**{text_frag}**"
                    elif is_italic:
                        text_frag = f"*{text_frag}*"
                    p_text += text_frag

            p_text = p_text.strip()
            if not p_text:
                continue

            if "Heading1" in style_val or style_val == "1":
                md_lines.append(f"\n## {p_text}\n")
            elif "Heading2" in style_val or style_val == "2":
                md_lines.append(f"\n### {p_text}\n")
            elif "Heading3" in style_val or style_val == "3":
                md_lines.append(f"\n#### {p_text}\n")
            elif "List" in style_val or "Bullet" in style_val:
                md_lines.append(f"- {p_text}")
            else:
                md_lines.append(f"{p_text}\n")

        elif tag == "tbl":
            # Extract table
            rows = elem.findall(".//w:tr", ns)
            table_data: list[list[str]] = []
            for tr in rows:
                row_cells: list[str] = []
                for tc in tr.findall(".//w:tc", ns):
                    tc_text = " ".join("".join(tc.itertext()).split())
                    row_cells.append(tc_text)
                if row_cells:
                    table_data.append(row_cells)

            if table_data:
                md_lines.append("")
                # Header
                headers = table_data[0]
                md_lines.append("| " + " | ".join(headers) + " |")
                md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for row in table_data[1:]:
                    # Pad cells if necessary
                    padded = row + [""] * (len(headers) - len(row))
                    md_lines.append("| " + " | ".join(padded[: len(headers)]) + " |")
                md_lines.append("")

    return "\n".join(md_lines)


# =====================================================================
# PowerPoint (.pptx) Extraction (100% Stdlib OpenXML)
# =====================================================================
def convert_pptx_to_md(pptx_path: Path, max_slides: int | None = None) -> str:
    try:
        with zipfile.ZipFile(pptx_path, "r") as z:
            slide_names = sorted(
                [n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")],
                key=lambda s: int(re.search(r"\d+", s).group(0)) if re.search(r"\d+", s) else 0,
            )
            if max_slides:
                slide_names = slide_names[:max_slides]

            md_lines: list[str] = [f"# {pptx_path.stem} (Presentation)\n"]

            for idx, sname in enumerate(slide_names, 1):
                slide_xml = z.read(sname)
                tree = ET.fromstring(slide_xml)
                ns = {
                    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
                    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
                }

                texts: list[str] = []
                for p_elem in tree.findall(".//a:p", ns):
                    line_text = "".join(t.text for t in p_elem.findall(".//a:t", ns) if t.text).strip()
                    if line_text:
                        texts.append(line_text)

                md_lines.append(f"## Slide {idx}")
                if texts:
                    title = texts[0]
                    md_lines.append(f"**Title**: {title}\n")
                    for t in texts[1:]:
                        md_lines.append(f"- {t}")
                else:
                    md_lines.append("_[Blank Slide]_")
                md_lines.append("\n")

        return "\n".join(md_lines)
    except Exception as e:
        return f"# Error reading PPTX {pptx_path.name}: {e}\n"


# =====================================================================
# Excel (.xlsx) & CSV Extraction (100% Stdlib)
# =====================================================================
def convert_csv_to_md(csv_path: Path, max_rows: int = 50) -> str:
    md_lines: list[str] = [f"# {csv_path.name} (CSV)\n"]
    try:
        content = csv_path.read_text(encoding="utf-8", errors="replace")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return md_lines[0] + "_[Empty CSV]_"

        headers = rows[0]
        md_lines.append("| " + " | ".join(headers) + " |")
        md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for r in rows[1 : max_rows + 1]:
            padded = r + [""] * (len(headers) - len(r))
            md_lines.append("| " + " | ".join(padded[: len(headers)]) + " |")

        if len(rows) > max_rows + 1:
            md_lines.append(f"\n_... [{len(rows) - max_rows - 1} rows truncated for token efficiency]_")

        return "\n".join(md_lines)
    except Exception as e:
        return f"# Error reading CSV {csv_path.name}: {e}\n"


def convert_xlsx_to_md(xlsx_path: Path, max_rows: int = 50) -> str:
    try:
        with zipfile.ZipFile(xlsx_path, "r") as z:
            # Parse shared strings
            shared_strings: list[str] = []
            if "xl/sharedStrings.xml" in z.namelist():
                ss_tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                ns_ss = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                for si in ss_tree.findall(".//x:si", ns_ss):
                    t_elem = si.find(".//x:t", ns_ss)
                    shared_strings.append(t_elem.text if t_elem is not None and t_elem.text else "")

            # Parse sheets
            sheet_names = [n for n in z.namelist() if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")]
            md_lines: list[str] = [f"# {xlsx_path.stem} (Spreadsheet)\n"]

            ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

            for sidx, sname in enumerate(sheet_names, 1):
                sheet_tree = ET.fromstring(z.read(sname))
                sheet_rows: list[list[str]] = []

                for r in sheet_tree.findall(".//x:row", ns):
                    cells: list[str] = []
                    for c in r.findall(".//x:c", ns):
                        t_type = c.attrib.get("t", "")
                        v_elem = c.find("x:v", ns)
                        val = ""
                        if v_elem is not None and v_elem.text:
                            if t_type == "s" and v_elem.text.isdigit():
                                idx = int(v_elem.text)
                                val = shared_strings[idx] if idx < len(shared_strings) else v_elem.text
                            else:
                                val = v_elem.text
                        cells.append(val)
                    if cells:
                        sheet_rows.append(cells)

                md_lines.append(f"## Sheet {sidx}\n")
                if not sheet_rows:
                    md_lines.append("_[Empty Sheet]_\n")
                    continue

                # Format as table
                headers = sheet_rows[0]
                md_lines.append("| " + " | ".join(headers) + " |")
                md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

                for r in sheet_rows[1 : max_rows + 1]:
                    padded = r + [""] * (len(headers) - len(r))
                    md_lines.append("| " + " | ".join(padded[: len(headers)]) + " |")

                if len(sheet_rows) > max_rows + 1:
                    md_lines.append(f"\n_... [{len(sheet_rows) - max_rows - 1} rows truncated]_")
                md_lines.append("\n")

        return "\n".join(md_lines)
    except Exception as e:
        return f"# Error reading XLSX {xlsx_path.name}: {e}\n"


# =====================================================================
# Jupyter Notebook (.ipynb) Extraction
# =====================================================================
def convert_ipynb_to_md(ipynb_path: Path) -> str:
    try:
        content = json.loads(ipynb_path.read_text(encoding="utf-8", errors="replace"))
        cells = content.get("cells", [])
        md_lines: list[str] = [f"# {ipynb_path.stem} (Jupyter Notebook)\n"]

        for i, cell in enumerate(cells, 1):
            cell_type = cell.get("cell_type", "code")
            source = "".join(cell.get("source", []))

            if cell_type == "markdown":
                md_lines.append(f"{source}\n")
            elif cell_type == "code":
                md_lines.append(f"```python\n# In [{i}]\n{source}\n```")
                # Outputs
                outputs = cell.get("outputs", [])
                out_texts: list[str] = []
                for out in outputs:
                    if "text" in out:
                        out_texts.append("".join(out["text"]))
                    elif "data" in out and "text/plain" in out["data"]:
                        out_texts.append("".join(out["data"]["text/plain"]))
                if out_texts:
                    joined_out = "".join(out_texts).strip()
                    if joined_out:
                        md_lines.append(f"```text\n# Output [{i}]:\n{joined_out[:500]}\n```")
                md_lines.append("")

        return "\n".join(md_lines)
    except Exception as e:
        return f"# Error reading IPYNB {ipynb_path.name}: {e}\n"


# =====================================================================
# HTML Extraction
# =====================================================================
class SimpleHTMLToMarkdown(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.output: list[str] = []
        self.tag_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tag_stack.append(tag.lower())
        if tag.lower() in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.output.append("\n" + ("#" * level) + " ")
        elif tag.lower() == "p":
            self.output.append("\n")
        elif tag.lower() == "li":
            self.output.append("\n- ")
        elif tag.lower() == "tr":
            self.output.append("\n| ")

    def handle_endtag(self, tag: str) -> None:
        if self.tag_stack and self.tag_stack[-1] == tag.lower():
            self.tag_stack.pop()
        if tag.lower() in ("p", "h1", "h2", "h3", "h4", "h5", "h6"):
            self.output.append("\n")
        elif tag.lower() in ("td", "th"):
            self.output.append(" | ")

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if clean:
            self.output.append(clean + " ")


def convert_html_to_md(html_path: Path) -> str:
    try:
        raw_html = html_path.read_text(encoding="utf-8", errors="replace")
        # Strip script and style tags
        clean_html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
        parser = SimpleHTMLToMarkdown()
        parser.feed(clean_html)
        return "".join(parser.output)
    except Exception as e:
        return f"# Error reading HTML {html_path.name}: {e}\n"


# =====================================================================
# Main Dispatcher
# =====================================================================
def convert_file_to_markdown(
    file_path: Path,
    max_pages: int | None = None,
    max_lines: int | None = None,
    include_meta: bool = False,
) -> str:
    """Universal dispatcher that converts any supported document into structured Markdown."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        result = convert_pdf_to_md(file_path, max_pages=max_pages)
    elif suffix in (".docx", ".doc"):
        result = convert_docx_to_md(file_path)
    elif suffix in (".pptx", ".ppt"):
        result = convert_pptx_to_md(file_path, max_slides=max_pages)
    elif suffix == ".xlsx":
        result = convert_xlsx_to_md(file_path)
    elif suffix in (".csv", ".tsv"):
        result = convert_csv_to_md(file_path)
    elif suffix == ".ipynb":
        result = convert_ipynb_to_md(file_path)
    elif suffix in (".html", ".htm"):
        result = convert_html_to_md(file_path)
    elif suffix == ".json":
        try:
            data = json.loads(file_path.read_text(encoding="utf-8", errors="replace"))
            result = f"```json\n{json.dumps(data, indent=2)}\n```"
        except Exception:
            result = file_path.read_text(encoding="utf-8", errors="replace")
    else:
        # Fallback to reading as plain text/code
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            result = f"```{suffix.lstrip('.')}\n{text}\n```"
        except Exception as e:
            result = f"# Error reading file {file_path.name}: {e}\n"

    if include_meta:
        size_kb = file_path.stat().st_size / 1024
        line_count = len(result.splitlines())
        char_count = len(result)
        meta_block = (
            f"---\n"
            f"document: {file_path.name}\n"
            f"size_kb: {size_kb:.1f}\n"
            f"lines: {line_count}\n"
            f"chars: {char_count}\n"
            f"---\n\n"
        )
        result = meta_block + result

    if max_lines:
        lines = result.splitlines()
        if len(lines) > max_lines:
            result = "\n".join(lines[:max_lines]) + f"\n\n_... [{len(lines) - max_lines} lines truncated for token efficiency]_"

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Universal Document to Structured Markdown Converter (PDF, DOCX, PPTX, XLSX, CSV, IPYNB, HTML)"
    )
    parser.add_argument("target", help="Path to document file to convert")
    parser.add_argument("--output", "-o", help="Output file path (default: print to stdout)")
    parser.add_argument("--max-pages", "-p", type=int, default=None, help="Maximum pages/slides/sheets to parse")
    parser.add_argument("--max-lines", "-l", type=int, default=None, help="Maximum output lines to emit")
    parser.add_argument("--meta", action="store_true", help="Prepend document YAML frontmatter metadata")

    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    if not target_path.exists():
        print(f"Error: Target file does not exist: {target_path}", file=sys.stderr)
        return 1

    md_output = convert_file_to_markdown(
        target_path,
        max_pages=args.max_pages,
        max_lines=args.max_lines,
        include_meta=args.meta,
    )

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_output, encoding="utf-8")
        print(f"[OK] Converted {target_path.name} -> {out_path}")
    else:
        sys.stdout.write(md_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

