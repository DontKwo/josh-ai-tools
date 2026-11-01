#!/usr/bin/env python3
"""Unit tests for boost_types.py script."""
import ast
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.boost_types import (
    boost_file,
    boost_function_signature,
    collect_return_types,
    infer_literal_type,
    infer_return_annotation,
)


class TestBoostTypes(unittest.TestCase):
    """Test suite for type annotation inference and preservation."""

    def test_infer_literal_type_primitives(self) -> None:
        """Verify inference for bool, int, float, str, bytes, and None."""
        self.assertEqual(infer_literal_type(ast.parse("True").body[0].value), "bool")
        self.assertEqual(infer_literal_type(ast.parse("False").body[0].value), "bool")
        self.assertEqual(infer_literal_type(ast.parse("42").body[0].value), "int")
        self.assertEqual(infer_literal_type(ast.parse("3.14").body[0].value), "float")
        self.assertEqual(infer_literal_type(ast.parse("'hello'").body[0].value), "str")
        self.assertEqual(infer_literal_type(ast.parse("b'data'").body[0].value), "bytes")
        self.assertEqual(infer_literal_type(ast.parse("None").body[0].value), "None")

    def test_infer_literal_type_containers(self) -> None:
        """Verify inference for list, dict, set, and tuple."""
        self.assertEqual(infer_literal_type(ast.parse("[]").body[0].value), "list")
        self.assertEqual(infer_literal_type(ast.parse("{}").body[0].value), "dict")
        self.assertEqual(infer_literal_type(ast.parse("{1, 2}").body[0].value), "set")
        self.assertEqual(infer_literal_type(ast.parse("()").body[0].value), "tuple")
        self.assertIsNone(infer_literal_type(ast.parse("custom_var").body[0].value))

    def test_collect_return_types_single(self) -> None:
        """Verify collection from a function with a single return statement."""
        code = "def sample() -> None:\n    return 'result'\n"
        tree = ast.parse(code)
        fn_node = tree.body[0]
        self.assertIsInstance(fn_node, ast.FunctionDef)
        return_types = collect_return_types(fn_node)
        self.assertEqual(return_types, ["str"])

    def test_collect_return_types_multiple_consistent(self) -> None:
        """Verify collection from multiple returns of the same type."""
        code = (
            "def sample(flag: bool):\n"
            "    if flag:\n"
            "        return 1\n"
            "    return 2\n"
        )
        tree = ast.parse(code)
        fn_node = tree.body[0]
        self.assertIsInstance(fn_node, ast.FunctionDef)
        return_types = collect_return_types(fn_node)
        self.assertEqual(return_types, ["int", "int"])
        inferred = infer_return_annotation(fn_node)
        self.assertEqual(inferred, "int")

    def test_collect_return_types_nullable(self) -> None:
        """Verify nullable return handling yielding str | None."""
        code = (
            "def sample(flag: bool):\n"
            "    if flag:\n"
            "        return 'valid'\n"
            "    return None\n"
        )
        tree = ast.parse(code)
        fn_node = tree.body[0]
        self.assertIsInstance(fn_node, ast.FunctionDef)
        return_types = collect_return_types(fn_node)
        self.assertEqual(return_types, ["str", "None"])
        inferred = infer_return_annotation(fn_node)
        self.assertEqual(inferred, "str | None")

    def test_preserve_existing_annotations(self) -> None:
        """Verify existing annotations are preserved and never overwritten."""
        code = "def sample(x: int = 5, y: str = 'default') -> bool:\n    return True\n"
        tree = ast.parse(code)
        fn_node = tree.body[0]
        self.assertIsInstance(fn_node, ast.FunctionDef)
        lines = code.splitlines(keepends=True)
        result = boost_function_signature(fn_node, lines)
        self.assertIsNone(result)

    def test_skip_self_and_cls_parameters(self) -> None:
        """Verify self and cls parameters are not annotated."""
        code = (
            "class SampleClass:\n"
            "    def method(self, count=10):\n"
            "        return count\n"
            "    @classmethod\n"
            "    def class_method(cls, name='agent'):\n"
            "        return name\n"
        )
        tree = ast.parse(code)
        class_node = tree.body[0]
        self.assertIsInstance(class_node, ast.ClassDef)
        lines = code.splitlines(keepends=True)

        method_node = class_node.body[0]
        self.assertIsInstance(method_node, ast.FunctionDef)
        method_boost = boost_function_signature(method_node, lines)
        self.assertIsNotNone(method_boost)
        if method_boost:
            self.assertIn("self, count: int = 10", method_boost[1])
            self.assertNotIn("self:", method_boost[1])

        cls_node = class_node.body[1]
        self.assertIsInstance(cls_node, ast.FunctionDef)
        cls_boost = boost_function_signature(cls_node, lines)
        self.assertIsNotNone(cls_boost)
        if cls_boost:
            self.assertIn("cls, name: str = 'agent'", cls_boost[1])
            self.assertNotIn("cls:", cls_boost[1])

    def test_ast_syntax_roundtrip_safety_check(self) -> None:
        """Verify AST syntax round-trip check prevents invalid modifications."""
        code = "def sample(x=10):\n    return x\n"
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as temp_file:
            temp_file.write(code)
            path = Path(temp_file.name)

        try:
            original_parse = ast.parse

            def mock_parse(src: str, *args: object, **kwargs: object) -> ast.AST:
                if "x: int" in src:
                    raise SyntaxError("Simulated invalid syntax generation")
                return original_parse(src, *args, **kwargs)

            with patch("ast.parse", side_effect=mock_parse):
                count, items = boost_file(path, fix=True)
                self.assertEqual(count, 0)
                self.assertEqual(items, [])

            # Verify file content remains unchanged
            content = path.read_text(encoding="utf-8")
            self.assertEqual(content, code)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
