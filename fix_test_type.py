with open("tests/test_smart_test_runner.py", "r") as f:
    content = f.read()

content = content.replace(
    "def test_find_impacted_tests(self, mock_cwd) -> None:",
    "def test_find_impacted_tests(self, mock_cwd: unittest.mock.MagicMock) -> None:"
)

with open("tests/test_smart_test_runner.py", "w") as f:
    f.write(content)
