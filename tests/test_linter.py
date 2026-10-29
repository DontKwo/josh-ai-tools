"""Unit test suite for claudemd_linter, lint_fixer, repo_map, and clean_encoding."""
import tempfile
import unittest
from pathlib import Path

from scripts.claudemd_linter import scan_file, noqa_codes, suppressed, parse_cli_args, LEVEL_RULES
from scripts.lint_fixer import fix_line, UNICODE_REPLACEMENTS, condense_docstrings
from scripts.repo_map import generate_map
from scripts.clean_encoding import clean_content
from scripts.prune_dead_code import find_unused_imports, prune_unused_imports_in_file
from scripts.boost_types import boost_file
from scripts.check_dependencies import scan_dependencies
from scripts.to_markdown import convert_file_to_markdown
from scripts.dir_overview import render_tree
from scripts.fast_search import search_in_file
from scripts.redact_diff import redact_diff_content
from scripts.rollback import save_checkpoint, restore_checkpoint, list_checkpoints


class TestClaudemdLinter(unittest.TestCase):

    def _scan_snippet(self, code_str: str, suffix: str = ".py") -> list[int]:
        with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code_str)
            tmp_path = Path(temp_file.name)

        violations = []
        try:
            scan_file(tmp_path, violations)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        return [v[2] for v in violations]

    def test_rule_1_em_dash(self) -> None:
        codes = self._scan_snippet("x = 10 — y = 20\n")
        self.assertIn(1, codes)

    def test_rule_2_unicode(self) -> None:
        codes = self._scan_snippet("text = ‘curly quote’\n")
        self.assertIn(2, codes)

    def test_rule_3_emoji(self) -> None:
        codes = self._scan_snippet("print('hello 🚀')\n")
        self.assertIn(3, codes)

    def test_rule_4_ai_phrases(self) -> None:
        codes1 = self._scan_snippet("# Let's delve into this function\n")
        self.assertIn(4, codes1)

        codes2 = self._scan_snippet("# This stands as a testament to the architecture\n")
        self.assertIn(4, codes2)

        codes3 = self._scan_snippet("# It marks a pivotal moment in the codebase\n")
        self.assertIn(4, codes3)

    def test_rule_5_negative_parallelism(self) -> None:
        codes = self._scan_snippet("# It is not just fast, but it is reliable\n")
        self.assertIn(5, codes)

    def test_rule_9_bare_except(self) -> None:
        code = "try:\n    x = 1\nexcept:\n    pass\n"
        codes = self._scan_snippet(code)
        self.assertIn(9, codes)

    def test_rule_10_bare_pass(self) -> None:
        code = "def stub_func() -> None:\n    pass\n"
        codes = self._scan_snippet(code)
        self.assertIn(10, codes)

    def test_rule_11_missing_type_hints(self) -> None:
        code = "def add(a, b):\n    return a + b\n"
        codes = self._scan_snippet(code)
        self.assertIn(11, codes)

    def test_rule_14_mutable_default(self) -> None:
        code = "def append_val(val: int, target: list = []) -> list:\n    target.append(val)\n    return target\n"
        codes = self._scan_snippet(code)
        self.assertIn(14, codes)

    def test_rule_15_equality_none(self) -> None:
        code = "def check(x: int | None) -> bool:\n    return x == None\n"
        codes = self._scan_snippet(code)
        self.assertIn(15, codes)

    def test_rule_16_string_formatting(self) -> None:
        code = "def fmt(name: str) -> str:\n    return 'Hello %s' % name\n"
        codes = self._scan_snippet(code)
        self.assertIn(16, codes)

    def test_rule_17_comment_blocks(self) -> None:
        code = "# Line 1\n# Line 2\n# Line 3\nx = 1\n"
        codes = self._scan_snippet(code)
        self.assertIn(17, codes)

    def test_rule_17_comment_block_exemption(self) -> None:
        code = "# long-comment-ok\n# Line 1\n# Line 2\n# Line 3\nx = 1\n"
        codes = self._scan_snippet(code)
        self.assertNotIn(17, codes)

    def test_rule_24_todos(self) -> None:
        codes = self._scan_snippet("# TODO: Implement this later\nx = 1\n")
        self.assertIn(24, codes)

    def test_rule_25_print_statement(self) -> None:
        codes = self._scan_snippet("def run() -> None:\n    print('debug')\n")
        self.assertIn(25, codes)

    def test_noqa_suppression(self) -> None:
        # Line with print and noqa: 25
        codes = self._scan_snippet("def run() -> None:\n    print('debug')  # noqa: 25\n")
        self.assertNotIn(25, codes)

        # Line with generic noqa
        codes_all = self._scan_snippet("def run() -> None:\n    print('debug')  # noqa\n")
        self.assertNotIn(25, codes_all)

    def test_rule_38_variable_naming(self) -> None:
        bad_code = "def process_data(items: list[int]) -> int:\n    temp = 10\n    return temp\n"
        codes_bad = self._scan_snippet(bad_code)
        self.assertIn(38, codes_bad)

        good_code = "def process_data(items: list[int]) -> int:\n    total_count = 10\n    return total_count\n"
        codes_good = self._scan_snippet(good_code)
        self.assertNotIn(38, codes_good)

    def test_rule_39_collapsed_equation(self) -> None:
        bad_code = "def calc_result(a: float, b: float, c: float, d: float, e: float) -> float:\n    return a + b * c / d - e\n"
        codes_bad = self._scan_snippet(bad_code)
        self.assertIn(39, codes_bad)

        good_code = "def calc_result(a: float, b: float, c: float) -> float:\n    term = b * c\n    return a + term\n"
        codes_good = self._scan_snippet(good_code)
        self.assertNotIn(39, codes_good)

    def test_rule_40_docstring_bloat(self) -> None:
        bloated = 'def add(a: int, b: int) -> int:\n    """Add two numbers.\n\n    Args:\n        a: First.\n        b: Second.\n\n    Returns:\n        Sum.\n    """\n    return a + b\n'
        codes = self._scan_snippet(bloated)
        self.assertIn(40, codes)

    def test_rule_41_divider_banners(self) -> None:
        code = "########################################\nx = 1\n"
        codes = self._scan_snippet(code)
        self.assertIn(41, codes)

    def test_rule_42_loop_micro_optimization(self) -> None:
        code = "res = [y for x in range(10) if (y := x * 2) > 5]\n"
        codes = self._scan_snippet(code)
        self.assertIn(42, codes)

    def test_rule_43_missing_physical_units(self) -> None:
        bad_code = "PRESSURE = 101325\n"
        codes_bad = self._scan_snippet(bad_code)
        self.assertIn(43, codes_bad)

        good_code1 = "PRESSURE_PA = 101325\n"
        codes_good1 = self._scan_snippet(good_code1)
        self.assertNotIn(43, codes_good1)

        good_code2 = "PRESSURE = 101325  # Pa\n"
        codes_good2 = self._scan_snippet(good_code2)
        self.assertNotIn(43, codes_good2)

    def test_rule_44_artificial_equation_line_break(self) -> None:
        bad_code = "total = (\n    a + b\n    + c\n)\n"
        codes_bad = self._scan_snippet(bad_code)
        self.assertIn(44, codes_bad)

    def test_rule_45_overengineered_oop(self) -> None:
        code = "from abc import ABC\nclass BasePropulsion(ABC):\n    pass\ndef calc_thrust() -> float:\n    return 1.0\n"
        codes = self._scan_snippet(code)
        self.assertIn(45, codes)

    def test_cli_levels_and_filters(self) -> None:
        target, level, skip, only, flags = parse_cli_args(["src", "--level", "standard", "--skip", "1,2", "--no-ruff"])
        self.assertEqual(target, "src")
        self.assertEqual(level, "standard")
        self.assertEqual(skip, {1, 2})
        self.assertTrue(flags["no_ruff"])

        target2, level2, skip2, only2, flags2 = parse_cli_args(["--only", "38,39"])
        self.assertEqual(level2, "strict")
        self.assertEqual(only2, {38, 39})


class TestLintFixer(unittest.TestCase):

    def test_auto_fixer_skips_em_dash(self) -> None:
        line = "Sentence with em dash — must not change.\n"
        fixed, changes = fix_line(line, 1, Path("test.py"), fix_emojis=True)
        self.assertIn("—", fixed)  # Must still contain em dash
        self.assertEqual(len(changes), 0)

    def test_auto_fixer_rule_15(self) -> None:
        line = "    if val == None or val != None:\n"
        fixed, changes = fix_line(line, 1, Path("test.py"), fix_emojis=False)
        self.assertEqual(fixed, "    if val is None or val is not None:\n")
        self.assertEqual(len(changes), 2)

    def test_auto_fixer_rule_2_unicode(self) -> None:
        line = "title = “smart quotes and ellipsis…”\n"
        fixed, changes = fix_line(line, 1, Path("test.py"), fix_emojis=False)
        self.assertEqual(fixed, 'title = "smart quotes and ellipsis..."\n')
        self.assertGreater(len(changes), 0)

    def test_auto_fixer_rule_41_banner(self) -> None:
        line = "########################################\n"
        fixed, changes = fix_line(line, 1, Path("test.py"), fix_emojis=False, fix_banners=True)
        self.assertEqual(fixed, "# ---\n")
        self.assertGreater(len(changes), 0)

    def test_auto_fixer_rule_40_docstring(self) -> None:
        content = 'def helper():\n    """Quick sum.\n\n    Args:\n        x: value\n    """\n    return x\n'
        cleaned, count = condense_docstrings(content)
        self.assertEqual(count, 1)
        self.assertNotIn("Args:", cleaned)


class TestCleanEncoding(unittest.TestCase):

    def test_mojibake_replacement(self) -> None:
        corrupted = "Itâ€™s a test with â€œquotesâ€\x9d and Â° symbols."
        cleaned, changes = clean_content(corrupted)
        self.assertIn("It's", cleaned)
        self.assertIn('"quotes"', cleaned)
        self.assertIn("°", cleaned)
        self.assertGreater(len(changes), 0)




class TestRepoMap(unittest.TestCase):

    def test_symbol_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_file = Path(tmpdir) / "sample.py"
            sample_file.write_text("class MyService:\n    def execute(self, val: int) -> bool:\n        return True\n", encoding="utf-8")
            result = generate_map(Path(tmpdir))
            self.assertIn("class MyService", result)
            self.assertIn("def execute", result)


class TestPruneDeadCode(unittest.TestCase):

    def test_detect_and_prune_unused(self) -> None:
        code = "import os, sys\nfrom math import sqrt, sin\nprint(sqrt(4))\nprint(os.name)\n"
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code)
            tmp_path = Path(temp_file.name)

        try:
            unused = find_unused_imports(tmp_path)
            unused_names = {unused_item.symbol for unused_item in unused}
            self.assertIn("sys", unused_names)
            self.assertIn("sin", unused_names)
            self.assertNotIn("os", unused_names)
            self.assertNotIn("sqrt", unused_names)

            count, changes = prune_unused_imports_in_file(tmp_path, dry_run=False)
            self.assertEqual(count, 2)
            content = tmp_path.read_text(encoding="utf-8")
            self.assertIn("import os\n", content)
            self.assertIn("from math import sqrt\n", content)
            self.assertNotIn("sys", content)
            self.assertNotIn("sin", content)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_preserve_noqa(self) -> None:
        code = "import unused_mod  # noqa\nx = 1\n"
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code)
            tmp_path = Path(temp_file.name)

        try:
            unused = find_unused_imports(tmp_path)
            self.assertEqual(len(unused), 0)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


class TestBoostTypes(unittest.TestCase):

    def test_infer_defaults_and_return(self) -> None:
        code = "def calculate(count=10, name='guest', is_admin=False):\n    return True\n"
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code)
            tmp_path = Path(temp_file.name)

        try:
            count, items = boost_file(tmp_path, fix=True)
            self.assertEqual(count, 1)
            content = tmp_path.read_text(encoding="utf-8")
            self.assertIn("def calculate(count: int = 10, name: str = 'guest', is_admin: bool = False) -> bool:", content)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_skip_self_and_infer_none(self) -> None:
        code = "class Worker:\n    def run(self):\n        print('running')\n"
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code)
            tmp_path = Path(temp_file.name)

        try:
            count, items = boost_file(tmp_path, fix=True)
            self.assertEqual(count, 1)
            content = tmp_path.read_text(encoding="utf-8")
            self.assertIn("def run(self) -> None:", content)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


class TestCheckDependencies(unittest.TestCase):

    def test_detect_hallucinated_package(self) -> None:
        code = "import nonexistent_phantom_package_12345\nimport json\n"
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code)
            tmp_path = Path(temp_file.name)

        try:
            res = scan_dependencies(tmp_path)
            self.assertIn("nonexistent_phantom_package_12345", res["hallucinated"])
            self.assertNotIn("json", res["hallucinated"])
        finally:
            if tmp_path.exists():
                tmp_path.unlink()



class TestNewLinterRules(unittest.TestCase):

    def _scan_snippet(self, code_str: str, suffix: str = ".py") -> list[int]:
        with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as temp_file:
            temp_file.write(code_str)
            tmp_path = Path(temp_file.name)

        violations = []
        try:
            scan_file(tmp_path, violations)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        return [v[2] for v in violations]

    def test_rule_36_ai_metadata(self) -> None:
        codes1 = self._scan_snippet("# Reference :contentReference[oaicite:0]{index=0}\n")
        self.assertIn(36, codes1)

        codes2 = self._scan_snippet("# Based on [cite: 1] and turn0search0\n")
        self.assertIn(36, codes2)

        codes3 = self._scan_snippet("# Link: https://en.wikipedia.org?utm_source=chatgpt.com\n")
        self.assertIn(36, codes3)

    def test_rule_37_conversational_fluff(self) -> None:
        codes = self._scan_snippet("# Certainly! Here is the updated implementation\n")
        self.assertIn(37, codes)


class TestToMarkdown(unittest.TestCase):

    def test_csv_conversion(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as temp_file:
            temp_file.write("name,role\nAlice,Lead\nBob,Dev\n")
            tmp_path = Path(temp_file.name)

        try:
            res = convert_file_to_markdown(tmp_path)
            self.assertIn("| name | role |", res)
            self.assertIn("| Alice | Lead |", res)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_html_conversion(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as temp_file:
            temp_file.write("<h2>Module Architecture</h2><p>Overview of components.</p>")
            tmp_path = Path(temp_file.name)

        try:
            res = convert_file_to_markdown(tmp_path)
            self.assertIn("## Module Architecture", res)
            self.assertIn("Overview of components", res)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


class TestRedactDiff(unittest.TestCase):

    def test_redact_diff(self) -> None:
        sample_diff = (
            "diff --git a/app.py b/app.py\n"
            "index 1234..5678 100644\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -10,4 +10,4 @@ def calculate():\n"
            "     x = 1\n"
            "-    return x + 1\n"
            "+    return x + 2\n"
        )
        redacted, orig_lines, new_lines = redact_diff_content(sample_diff)
        self.assertIn("File: `app.py`", redacted)
        self.assertIn("Scope: `def calculate():`", redacted)
        self.assertIn("+    return x + 2", redacted)


class TestRollback(unittest.TestCase):

    def test_checkpoint_save_and_restore(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            f = ws / "data.txt"
            f.write_text("version 1", encoding="utf-8")

            # Save checkpoint
            cp_name = save_checkpoint(ws, "v1")
            cps = list_checkpoints(ws)
            self.assertEqual(len(cps), 1)

            # Modify file
            f.write_text("version 2 (corrupted by AI)", encoding="utf-8")
            self.assertEqual(f.read_text(encoding="utf-8"), "version 2 (corrupted by AI)")

            # Restore checkpoint
            success = restore_checkpoint(ws, cp_name)
            self.assertTrue(success)
            self.assertEqual(f.read_text(encoding="utf-8"), "version 1")


if __name__ == "__main__":
    unittest.main()



