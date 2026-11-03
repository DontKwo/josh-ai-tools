import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Any

# Ensure proper module resolution by dynamically appending the scripts/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from import_graph import build_dependency_graph, detect_cycles, get_module_name, parse_imports


class TestImportGraph(unittest.TestCase):
    """Test suite for import_graph.py functionality."""

    def setUp(self) -> None:
        """Set up temporary directory and mock files for testing."""
        self.temp_dir: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
        # Resolve to prevent Windows 8.3 short-name mismatches or symlink issues
        self.root_path: Path = Path(self.temp_dir.name).resolve()

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.temp_dir.cleanup()
        import importlib
        import sys
        if 'import_graph' in sys.modules:
            importlib.reload(sys.modules['import_graph'])

    def create_mock_file(self, rel_path: str, content: str) -> Path:
        """Create a mock Python file with the given content."""
        file_path: Path = self.root_path / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    def test_get_module_name(self) -> None:
        """Test module name extraction from file path."""
        file1: Path = self.root_path / "module_a.py"
        self.assertEqual(get_module_name(file1, self.root_path), "module_a")

        file2: Path = self.root_path / "pkg" / "module_b.py"
        self.assertEqual(get_module_name(file2, self.root_path), "pkg.module_b")

        file3: Path = self.root_path / "pkg" / "__init__.py"
        self.assertEqual(get_module_name(file3, self.root_path), "pkg")

    def test_parse_imports(self) -> None:
        """Test import parsing from AST."""
        content: str = "import os\nimport sys\nfrom typing import List\nfrom . import local_module\nfrom ..pkg import another_module"
        file_path: Path = self.create_mock_file("pkg/subpkg/module_c.py", content)
        # Parse imports requires parsing AST, checking node types
        imports: List[str] = parse_imports(file_path, self.root_path)

        self.assertIn("os", imports)
        self.assertIn("sys", imports)
        # the from alias gets 'typing' or 'typing.List' based on our simple ast visitor? No, node.module is 'typing'
        # actually node.module is 'typing' so if node.module: imports.append(f"{base}.{node.module}" if base else node.module)
        self.assertIn("typing", imports)
        self.assertIn("pkg.subpkg.local_module", imports)
        self.assertIn("pkg.pkg", imports)

    def test_build_dependency_graph(self) -> None:
        """Test building dependency graph."""
        self.create_mock_file("a.py", "import b\nimport c")
        self.create_mock_file("b.py", "import c")
        self.create_mock_file("c.py", "import os")

        graph: Dict[str, List[str]] = build_dependency_graph(self.root_path)
        self.assertIn("a", graph)
        self.assertIn("b", graph)
        self.assertIn("c", graph)

        self.assertIn("b", graph["a"])
        self.assertIn("c", graph["a"])
        self.assertIn("c", graph["b"])
        self.assertIn("os", graph["c"])

    def test_detect_cycles_no_cycle(self) -> None:
        """Test cycle detection on a graph without cycles."""
        self.create_mock_file("a.py", "import b\nimport c")
        self.create_mock_file("b.py", "import c")
        self.create_mock_file("c.py", "import os")

        graph: Dict[str, List[str]] = build_dependency_graph(self.root_path)
        cycles: List[List[str]] = detect_cycles(graph)
        self.assertEqual(len(cycles), 0)

    def test_detect_cycles_simple_cycle(self) -> None:
        """Test cycle detection on a simple cycle."""
        self.create_mock_file("a.py", "import b")
        self.create_mock_file("b.py", "import a")

        graph: Dict[str, List[str]] = build_dependency_graph(self.root_path)
        cycles: List[List[str]] = detect_cycles(graph)
        self.assertEqual(len(cycles), 1)
        self.assertCountEqual(cycles[0], ["a", "b"])

    def test_detect_cycles_complex(self) -> None:
        """Test cycle detection on a complex graph."""
        self.create_mock_file("a.py", "import b")
        self.create_mock_file("b.py", "import c")
        self.create_mock_file("c.py", "import a\nimport d")
        self.create_mock_file("d.py", "import e")
        self.create_mock_file("e.py", "import d")

        graph: Dict[str, List[str]] = build_dependency_graph(self.root_path)
        cycles: List[List[str]] = detect_cycles(graph)
        self.assertEqual(len(cycles), 2)
        # cycles should be ["a", "b", "c"] and ["d", "e"]

        cycle_sets = [set(c) for c in cycles]
        self.assertIn({"a", "b", "c"}, cycle_sets)
        self.assertIn({"d", "e"}, cycle_sets)

if __name__ == "__main__":
    unittest.main()
