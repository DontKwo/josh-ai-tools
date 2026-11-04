import unittest
import sys
import tempfile
from pathlib import Path
from typing import List

# Ensure scripts module is reachable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from unused_symbols import analyze_file

class TestUnusedSymbols(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name).resolve()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _create_file(self, filename: str, content: str) -> Path:
        filepath = self.temp_path / filename
        filepath.write_text(content, encoding='utf-8')
        return filepath

    def test_unused_private_function(self) -> None:
        content = """
def _unused():
    pass
"""
        filepath = self._create_file("test_unused_func.py", content)
        result = analyze_file(filepath)
        self.assertEqual(len(result), 1)
        self.assertIn("Unused private function '_unused'", result[0])

    def test_used_private_function(self) -> None:
        content = """
def _used():
    pass

def main():
    _used()
"""
        filepath = self._create_file("test_used_func.py", content)
        result = analyze_file(filepath)
        self.assertEqual(len(result), 0)

    def test_unused_local_variable(self) -> None:
        content = """
def main():
    x = 1
    y = 2
    print(y)
"""
        filepath = self._create_file("test_unused_var.py", content)
        result = analyze_file(filepath)
        self.assertEqual(len(result), 1)
        self.assertIn("Unused local variable 'x' in function 'main'", result[0])

    def test_used_local_variable(self) -> None:
        content = """
def main():
    x = 1
    print(x)
"""
        filepath = self._create_file("test_used_var.py", content)
        result = analyze_file(filepath)
        self.assertEqual(len(result), 0)

    def test_unused_argument(self) -> None:
        content = """
def main(arg1: int, arg2: str):
    print(arg1)
"""
        filepath = self._create_file("test_unused_arg.py", content)
        result = analyze_file(filepath)
        self.assertEqual(len(result), 1)
        self.assertIn("Unused local variable 'arg2' in function 'main'", result[0])

    def test_ignore_underscore_variables(self) -> None:
        content = """
def main():
    _x = 1
    _ = 2
"""
        filepath = self._create_file("test_underscore.py", content)
        result = analyze_file(filepath)
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    unittest.main()
