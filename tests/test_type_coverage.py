import unittest
import tempfile
from pathlib import Path
import sys

# Append scripts dir to path to import type_coverage
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import type_coverage

class TestTypeCoverage(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir).resolve()

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_coverage_calculation(self) -> None:
        test_file = self.temp_path / "test.py"
        test_file.write_text("""
def func1(a: int, b: str) -> bool:
    return True

def func2(x, y):
    pass

class MyClass:
    def method1(self, val: int) -> None:
        pass

    def method2(self, val):
        pass
        """, encoding="utf-8")

        visitor = type_coverage.analyze_file(str(test_file))

        self.assertEqual(visitor.functions_count, 4)
        self.assertEqual(visitor.params_count, 6)
        self.assertEqual(visitor.params_annotated, 3)
        self.assertEqual(visitor.returns_count, 4)
        self.assertEqual(visitor.returns_annotated, 2)

if __name__ == '__main__':
    unittest.main()
