import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from ast_complexity import compute_complexity, analyze_files, main

class TestASTComplexity(unittest.TestCase):
    def test_simple_function(self) -> None:
        source = "def foo() -> None:\n    pass\n"
        res = compute_complexity("test.py", source)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].complexity, 1)

    def test_if_statement(self) -> None:
        source = "def foo(x: int) -> None:\n    if x > 0:\n        pass\n"
        res = compute_complexity("test.py", source)
        self.assertEqual(res[0].complexity, 2)

    def test_for_loop(self) -> None:
        source = "def foo(x: list) -> None:\n    for i in x:\n        pass\n"
        res = compute_complexity("test.py", source)
        self.assertEqual(res[0].complexity, 2)

    def test_while_loop(self) -> None:
        source = "def foo() -> None:\n    while True:\n        pass\n"
        res = compute_complexity("test.py", source)
        self.assertEqual(res[0].complexity, 2)

    def test_except_handler(self) -> None:
        source = "def foo() -> None:\n    try:\n        pass\n    except Exception:\n        pass\n"
        res = compute_complexity("test.py", source)
        self.assertEqual(res[0].complexity, 2)

    def test_with_statement(self) -> None:
        source = "def foo() -> None:\n    with open('test.txt'):\n        pass\n"
        res = compute_complexity("test.py", source)
        self.assertEqual(res[0].complexity, 2)

    def test_bool_op(self) -> None:
        source = "def foo(x: int) -> None:\n    if x > 0 and x < 10:\n        pass\n"
        res = compute_complexity("test.py", source)
        self.assertEqual(res[0].complexity, 3)

    def test_multiple_bool_ops(self) -> None:
        source = "def foo(x: int) -> None:\n    if x > 0 and x < 10 or x == 20:\n        pass\n"
        res = compute_complexity("test.py", source)
        # if = 1, bool ops = 2 -> total complexity = 1 (base) + 1 (if) + 2 (bool ops) = 4
        self.assertEqual(res[0].complexity, 4)

    def test_async_function(self) -> None:
        source = "async def foo() -> None:\n    async with x:\n        async for y in z:\n            pass\n"
        res = compute_complexity("test.py", source)
        self.assertEqual(res[0].complexity, 3)

    def test_cli_max_complexity_exceeded(self) -> None:
        # Create a temp file to test analyze_files / main
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def foo() -> None:\n    if True:\n        if True:\n            pass\n")
            temp_path = f.name

        try:
            exit_code = main(["--max-complexity", "2", temp_path])
            self.assertEqual(exit_code, 1)
        finally:
            Path(temp_path).unlink()

    def test_cli_max_complexity_ok(self) -> None:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def foo() -> None:\n    if True:\n        pass\n")
            temp_path = f.name

        try:
            exit_code = main(["--max-complexity", "2", temp_path])
            self.assertEqual(exit_code, 0)
        finally:
            Path(temp_path).unlink()

if __name__ == "__main__":
    unittest.main()
