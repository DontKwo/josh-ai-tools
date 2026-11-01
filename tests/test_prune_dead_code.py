#!/usr/bin/env python3
"""Unit tests for scripts/prune_dead_code.py."""
import ast
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.prune_dead_code import (
    ASTUsageCollector,
    find_unused_imports,
    prune_unused_imports_in_file,
)


class TestPruneDeadCode(unittest.TestCase):
    """Test suite for dead code pruning and unused import detection."""

    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_ast_usage_collector_function_calls_and_attributes(self) -> None:
        """Verify identifier collection across calls and attribute accesses."""
        code = "result = math.sqrt(16)\ncustom_func(value=result)\n"
        tree = ast.parse(code)
        collector = ASTUsageCollector()
        collector.visit(tree)

        self.assertIn("math", collector.used_names)
        self.assertIn("custom_func", collector.used_names)
        self.assertIn("result", collector.used_names)

    def test_ast_usage_collector_type_annotations(self) -> None:
        """Verify identifier collection across AST annotations and string forwards."""
        code = "def process(item: CustomType, delayed: 'DeferredModel') -> None:\n    return None\n"
        tree = ast.parse(code)
        collector = ASTUsageCollector()
        collector.visit(tree)

        self.assertIn("CustomType", collector.used_names)
        self.assertIn("DeferredModel", collector.used_names)

    def test_ast_usage_collector_all_exports(self) -> None:
        """Verify preservation of symbols exported in __all__ definitions."""
        code_list = "__all__ = ['alpha', 'beta']\n"
        tree_list = ast.parse(code_list)
        collector_list = ASTUsageCollector()
        collector_list.visit(tree_list)
        self.assertEqual(collector_list.exported_names, {"alpha", "beta"})
        self.assertIn("alpha", collector_list.used_names)
        self.assertIn("beta", collector_list.used_names)

        code_set = "__all__ = {'gamma'}\n"
        tree_set = ast.parse(code_set)
        collector_set = ASTUsageCollector()
        collector_set.visit(tree_set)
        self.assertEqual(collector_set.exported_names, {"gamma"})
        self.assertIn("gamma", collector_set.used_names)

    def test_find_unused_imports_preserve_init(self) -> None:
        """Verify __init__.py files preserve re-exports without flagging."""
        init_file = self.temp_dir / "__init__.py"
        init_file.write_text("import unused_module\nfrom math import sin\n", encoding="utf-8")

        flagged_imports = find_unused_imports(init_file, preserve_init=True)
        self.assertEqual(flagged_imports, [])

    def test_find_unused_imports_top_level(self) -> None:
        """Verify unused top-level module imports are detected."""
        source_file = self.temp_dir / "top_level.py"
        source_file.write_text("import unused_module\nimport math\nprint(math.pi)\n", encoding="utf-8")

        flagged_imports = find_unused_imports(source_file)
        self.assertEqual(len(flagged_imports), 1)
        self.assertEqual(flagged_imports[0].symbol, "unused_module")
        self.assertFalse(flagged_imports[0].is_from_import)

    def test_find_unused_imports_from_imports(self) -> None:
        """Verify partially unused from-imports flag only unused symbols."""
        source_file = self.temp_dir / "from_import.py"
        source_file.write_text("from math import sin, unused_func\nprint(sin(0))\n", encoding="utf-8")

        flagged_imports = find_unused_imports(source_file)
        self.assertEqual(len(flagged_imports), 1)
        self.assertEqual(flagged_imports[0].symbol, "unused_func")
        self.assertTrue(flagged_imports[0].is_from_import)

    def test_find_unused_imports_noqa_and_pragma_ignored(self) -> None:
        """Verify lines with noqa or pragma annotations are ignored."""
        source_file = self.temp_dir / "ignored_imports.py"
        source_file.write_text(
            "import unused_one  # noqa\n"
            "from os import path  # pragma: no cover\n"
            "import regular_unused\n",
            encoding="utf-8",
        )

        flagged_imports = find_unused_imports(source_file)
        self.assertEqual(len(flagged_imports), 1)
        self.assertEqual(flagged_imports[0].symbol, "regular_unused")

    def test_prune_unused_imports_preserves_formatting_and_validity(self) -> None:
        """Verify pruning maintains indentation and valid AST syntax."""
        source_file = self.temp_dir / "format_test.py"
        source_file.write_text(
            "from math import cos, unused_symbol\n"
            "print(cos(0))\n",
            encoding="utf-8",
        )

        pruned_count, applied_changes = prune_unused_imports_in_file(source_file, dry_run=False)
        self.assertEqual(pruned_count, 1)
        self.assertTrue(len(applied_changes) > 0)

        updated_code = source_file.read_text(encoding="utf-8")
        self.assertEqual(updated_code, "from math import cos\nprint(cos(0))\n")
        # Verify valid AST parse
        parsed_tree = ast.parse(updated_code)
        self.assertIsNotNone(parsed_tree)

    def test_prune_unused_imports_ast_validation_failure_prevents_write(self) -> None:
        """Verify invalid AST prevents file overwrites during pruning."""
        source_file = self.temp_dir / "invalid_ast.py"
        initial_code = "import unused_module\nprint('hello')\n"
        source_file.write_text(initial_code, encoding="utf-8")

        original_ast_parse = ast.parse

        def mock_parse(source_str: str, *parse_args: object, **parse_kwargs: object) -> ast.AST:
            if "print('hello')" in source_str and "unused_module" not in source_str:
                raise SyntaxError("Simulated syntax failure")
            return original_ast_parse(source_str, *parse_args, **parse_kwargs)

        with patch("ast.parse", side_effect=mock_parse):
            pruned_count, applied_changes = prune_unused_imports_in_file(source_file, dry_run=False)
            self.assertEqual(pruned_count, 0)
            self.assertEqual(applied_changes, [])

        persisted_content = source_file.read_text(encoding="utf-8")
        self.assertEqual(persisted_content, initial_code)


if __name__ == "__main__":
    unittest.main()
