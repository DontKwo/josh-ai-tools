#!/usr/bin/env python3
"""Unit tests for check_variable_names.py script."""
import ast
import tempfile
import unittest
from pathlib import Path

from scripts.check_variable_names import is_descriptive_name, VariableAuditor


class TestCheckVariableNames(unittest.TestCase):

    def test_is_descriptive_name_allowed_single_chars(self) -> None:
        valid, msg = is_descriptive_name("i", "context")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_is_descriptive_name_dunder(self) -> None:
        valid, msg = is_descriptive_name("__name__", "context")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_is_descriptive_name_short(self) -> None:
        valid, msg = is_descriptive_name("ab", "context")
        self.assertFalse(valid)
        self.assertIn("too short", msg)

    def test_is_descriptive_name_vague(self) -> None:
        valid, msg = is_descriptive_name("data", "context")
        self.assertFalse(valid)
        self.assertIn("non-descriptive or generic", msg)

    def test_is_descriptive_name_valid(self) -> None:
        valid, msg = is_descriptive_name("user_id", "context")
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_variable_auditor(self) -> None:
        code = '''
def my_func(foo: int, p: str, *, x: float) -> None:
    temp = 1
    long_var_name = 2
    my_list = [i for i in range(10)]
    valid_var = 3
'''
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            path = Path(f.name)

        try:
            tree = ast.parse(code)
            auditor = VariableAuditor(path)
            auditor.visit(tree)

            violations = auditor.violations
            self.assertEqual(len(violations), 3)

            names = [v[1] for v in violations]
            self.assertIn("foo", names)
            self.assertIn("temp", names)
            self.assertIn("my_list", names)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
