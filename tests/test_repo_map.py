"""Unit test suite for scripts/repo_map.py."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from repo_map import (
    DEFAULT_SKIP_DIRS,
    extract_python_symbols,
    extract_regex_symbols,
    generate_map,
    render_repo_map,
)


class TestRepoMapPythonAst(unittest.TestCase):
    """Test AST symbol extraction for Python files."""

    def test_imports_extraction(self) -> None:
        source_code = (
            "import os\n"
            "import sys, math\n"
            "from pathlib import Path, PurePath\n"
            "from typing import Optional\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(source_code)
            temp_path = Path(temp_file.name).resolve()

        try:
            symbols = extract_python_symbols(temp_path)
            self.assertIn("os", symbols["imports"])
            self.assertIn("sys", symbols["imports"])
            self.assertIn("math", symbols["imports"])
            self.assertIn("pathlib: Path, PurePath", symbols["imports"])
            self.assertIn("typing: Optional", symbols["imports"])
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_function_signatures(self) -> None:
        source_code = (
            "def calculate_total(quantity: int, unit_price: float) -> float:\n"
            "    '''Calculate total purchase price.'''\n"
            "    return quantity * unit_price\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(source_code)
            temp_path = Path(temp_file.name).resolve()

        try:
            symbols = extract_python_symbols(temp_path)
            functions = symbols["functions"]
            self.assertEqual(len(functions), 1)
            sig, doc = functions[0]
            self.assertEqual(sig, "def calculate_total(quantity: int, unit_price: float) -> float")
            self.assertEqual(doc, "Calculate total purchase price.")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_async_function_signatures(self) -> None:
        source_code = (
            "async def fetch_payload(endpoint: str, timeout_seconds: int) -> dict:\n"
            "    '''Fetch remote response payload asynchronously.'''\n"
            "    return {}\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(source_code)
            temp_path = Path(temp_file.name).resolve()

        try:
            symbols = extract_python_symbols(temp_path)
            functions = symbols["functions"]
            self.assertEqual(len(functions), 1)
            sig, doc = functions[0]
            self.assertEqual(sig, "async def fetch_payload(endpoint: str, timeout_seconds: int) -> dict")
            self.assertEqual(doc, "Fetch remote response payload asynchronously.")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_class_definitions(self) -> None:
        source_code = (
            "class PipelineProcessor(BaseService, LoggableMixin):\n"
            "    '''Core pipeline execution service.'''\n"
            "    def configure_runner(self, settings: dict) -> bool:\n"
            "        return True\n"
            "    async def run_step(self, step_id: str) -> None:\n"
            "        return None\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(source_code)
            temp_path = Path(temp_file.name).resolve()

        try:
            symbols = extract_python_symbols(temp_path)
            classes = symbols["classes"]
            class_key = "PipelineProcessor(BaseService, LoggableMixin)"
            self.assertIn(class_key, classes)
            doc, methods = classes[class_key]
            self.assertEqual(doc, "Core pipeline execution service.")
            self.assertEqual(len(methods), 2)
            self.assertEqual(methods[0], "def configure_runner(self, settings: dict) -> bool")
            self.assertEqual(methods[1], "async def run_step(self, step_id: str) -> None")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_invalid_python_syntax(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as temp_file:
            temp_file.write("def invalid syntax (:\n")
            temp_path = Path(temp_file.name).resolve()

        try:
            symbols = extract_python_symbols(temp_path)
            self.assertEqual(symbols, {})
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestRepoMapRegexSymbols(unittest.TestCase):
    """Test regex symbol extraction fallback for non-Python languages."""

    def test_javascript_typescript_symbols(self) -> None:
        source_code = (
            "export class DataManager {\n"
            "}\n"
            "class HelperUtil {\n"
            "}\n"
            "export async function fetchRemote(url) {\n"
            "}\n"
            "function processLocal(item) {\n"
            "}\n"
            "export const formatRecord = (record) => {\n"
            "};\n"
            "export let counter = 0;\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".ts", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(source_code)
            temp_path = Path(temp_file.name).resolve()

        try:
            symbols = extract_regex_symbols(temp_path)
            self.assertIn("DataManager", symbols["classes"])
            self.assertIn("HelperUtil", symbols["classes"])
            self.assertIn("fetchRemote", symbols["functions"])
            self.assertIn("processLocal", symbols["functions"])
            self.assertIn("formatRecord", symbols["functions"])
            self.assertIn("DataManager", symbols["exports"])
            self.assertIn("counter", symbols["exports"])
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_rust_symbols(self) -> None:
        source_code = (
            "pub struct ConfigParser {\n"
            "    timeout: u64,\n"
            "}\n"
            "enum ExecutionStatus {\n"
            "    Active,\n"
            "}\n"
            "trait Streamable {\n"
            "}\n"
            "impl Streamable for ConfigParser {\n"
            "}\n"
            "impl ExecutionStatus {\n"
            "}\n"
            "pub async fn start_service() -> bool {\n"
            "    true\n"
            "}\n"
            "fn compute_hash(seed: &[u8]) -> u32 {\n"
            "    0\n"
            "}\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".rs", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(source_code)
            temp_path = Path(temp_file.name).resolve()

        try:
            symbols = extract_regex_symbols(temp_path)
            self.assertIn("ConfigParser", symbols["classes"])
            self.assertIn("ExecutionStatus", symbols["classes"])
            self.assertIn("Streamable", symbols["classes"])
            self.assertIn("start_service", symbols["functions"])
            self.assertIn("compute_hash", symbols["functions"])
            # Validate impl block duplication isn't an issue but it's captured
            self.assertEqual(symbols["classes"].count("ConfigParser"), 2)
            self.assertEqual(symbols["classes"].count("ExecutionStatus"), 2)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_cpp_symbols(self) -> None:
        source_code = (
            "namespace MyNamespace {\n"
            "    class MyClass {\n"
            "        void my_method();\n"
            "        MyClass();\n"
            "        ~MyClass();\n"
            "    };\n"
            "}\n"
            "struct MyStruct {};\n"
            "void global_function() {}\n"
            "int* get_pointer() {}\n"
            "const std::string& get_string() {}\n"
            "static inline void inline_func() {}\n"
            "MyClass::MyClass() {}\n"
            "MyClass::~MyClass() {}\n"
            "void MyNamespace::MyClass::my_method() {}\n"
        )
        for ext in [".cpp", ".hpp", ".h"]:
            with tempfile.NamedTemporaryFile("w", suffix=ext, delete=False, encoding="utf-8") as temp_file:
                temp_file.write(source_code)
                temp_path = Path(temp_file.name).resolve()

            try:
                symbols = extract_regex_symbols(temp_path)
                self.assertIn("MyNamespace", symbols["classes"])
                self.assertIn("MyClass", symbols["classes"])
                self.assertIn("MyStruct", symbols["classes"])
                self.assertIn("my_method", symbols["functions"])
                self.assertIn("MyClass", symbols["functions"])
                self.assertIn("~MyClass", symbols["functions"])
                self.assertIn("global_function", symbols["functions"])
                self.assertIn("get_pointer", symbols["functions"])
                self.assertIn("get_string", symbols["functions"])
                self.assertIn("inline_func", symbols["functions"])
                self.assertIn("MyClass::MyClass", symbols["functions"])
                self.assertIn("MyClass::~MyClass", symbols["functions"])
                self.assertIn("MyNamespace::MyClass::my_method", symbols["functions"])
            finally:
                if temp_path.exists():
                    temp_path.unlink()

    def test_go_symbols(self) -> None:
        source_code = (
            "package main\n"
            "type ServerConfig struct {\n"
            "    Port int\n"
            "}\n"
            "type Handler interface {\n"
            "    ServeHTTP()\n"
            "}\n"
            "func NewServer(port int) *ServerConfig {\n"
            "    return &ServerConfig{Port: port}\n"
            "}\n"
            "func (server_config *ServerConfig) Start() error {\n"
            "    return nil\n"
            "}\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".go", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(source_code)
            temp_path = Path(temp_file.name).resolve()

        try:
            symbols = extract_regex_symbols(temp_path)
            self.assertIn("ServerConfig", symbols["classes"])
            self.assertIn("Handler", symbols["classes"])
            self.assertIn("NewServer", symbols["functions"])
            self.assertIn("Start", symbols["functions"])
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_empty_or_non_existent_file(self) -> None:
        missing_path = Path("non_existent_symbol_file.rs")
        symbols = extract_regex_symbols(missing_path)
        self.assertEqual(symbols, {})


class TestRepoMapTreeFormatting(unittest.TestCase):
    """Test tree formatting, rendering, and directory exclusions."""

    def test_render_repo_map_with_python_and_regex(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_str:
            root_path = Path(temp_dir_str).resolve()
            src_dir = root_path / "src"
            src_dir.mkdir()

            py_file = src_dir / "service.py"
            py_file.write_text(
                "import os\n"
                "class WorkerTask:\n"
                "    '''Worker task runner.'''\n"
                "    def execute(self) -> None:\n"
                "        return None\n"
                "def main_entry() -> None:\n"
                "    '''Entrypoint.'''\n"
                "    return None\n",
                encoding="utf-8",
            )

            ts_file = src_dir / "client.ts"
            ts_file.write_text(
                "export class ApiClient {}\n"
                "export async function requestData() {}\n",
                encoding="utf-8",
            )

            map_output = render_repo_map(root_path)
            self.assertIn(f"# Codebase Symbol & Dependency Map: {root_path.name}", map_output)
            self.assertIn("service.py:", map_output)
            self.assertIn("class WorkerTask - Worker task runner.", map_output)
            self.assertIn("def execute(self) -> None", map_output)
            self.assertIn("def main_entry() -> None - Entrypoint.", map_output)
            self.assertIn("client.ts:", map_output)
            self.assertIn("class/type ApiClient", map_output)
            self.assertIn("fn requestData", map_output)

    def test_default_skip_dirs_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_str:
            root_path = Path(temp_dir_str).resolve()
            for skip_name in DEFAULT_SKIP_DIRS:
                skip_dir = root_path / skip_name
                skip_dir.mkdir(parents=True, exist_ok=True)
                hidden_file = skip_dir / f"hidden_{skip_name.replace('.', '_')}.py"
                hidden_file.write_text("def secret_func() -> None:\n    pass\n", encoding="utf-8")

            valid_file = root_path / "visible_task.py"
            valid_file.write_text("def visible_func() -> None:\n    pass\n", encoding="utf-8")

            map_output = render_repo_map(root_path)
            self.assertIn("visible_task.py:", map_output)
            self.assertIn("def visible_func() -> None", map_output)

            for skip_name in DEFAULT_SKIP_DIRS:
                self.assertNotIn(f"hidden_{skip_name.replace('.', '_')}.py", map_output)

    def test_generate_map_max_lines_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir_str:
            root_path = Path(temp_dir_str).resolve()
            for index in range(20):
                file_path = root_path / f"module_{index:02d}.py"
                file_path.write_text(
                    f"class Class{index:02d}:\n"
                    f"    def action_{index:02d}(self) -> None:\n"
                    f"        return None\n",
                    encoding="utf-8",
                )

            budget_output = generate_map(root_path, max_lines=15)
            self.assertIn("... [truncated to fit token budget]", budget_output)


if __name__ == "__main__":
    unittest.main()
