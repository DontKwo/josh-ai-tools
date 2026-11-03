import unittest
import tempfile
import sys
from pathlib import Path

# Add scripts directory to sys.path for importing env_validator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from env_validator import parse_line, validate_type, validate_env

class TestEnvValidator(unittest.TestCase):
    """Test cases for the env validator."""

    def test_parse_line(self) -> None:
        """Test parsing an env file line."""
        k, v, t = parse_line("FOO=bar # type: int")
        self.assertEqual(k, "FOO")
        self.assertEqual(v, "bar")
        self.assertEqual(t, "int")

        k, v, t = parse_line("BAZ=123")
        self.assertEqual(k, "BAZ")
        self.assertEqual(v, "123")
        self.assertEqual(t, "")

        k, v, t = parse_line("# just a comment")
        self.assertEqual(k, "")

    def test_validate_type(self) -> None:
        """Test type validation."""
        self.assertTrue(validate_type("123", "int"))
        self.assertFalse(validate_type("abc", "int"))

        self.assertTrue(validate_type("true", "bool"))
        self.assertTrue(validate_type("yes", "bool"))
        self.assertFalse(validate_type("maybe", "bool"))

        self.assertTrue(validate_type("http://example.com", "url"))
        self.assertFalse(validate_type("ftp://example.com", "url"))

    def test_validate_env(self) -> None:
        """Test full env validation with files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()

            ex_file = temp_path / ".env.example"
            ex_file.write_text("URL=http://x.com # type: url\nNUM=1 # type: int\n")

            env_file = temp_path / ".env"
            env_file.write_text("URL=http://test.com\nNUM=123\nEXTRA=bad\n")

            errors = validate_env(env_file, ex_file)
            self.assertIn("Unexpected key: EXTRA", errors)
            self.assertEqual(len(errors), 1)

            # Test missing and invalid types
            env_file.write_text("URL=bad_url\n")
            errors = validate_env(env_file, ex_file)
            self.assertIn("Missing required key: NUM", errors)
            self.assertIn("Invalid type for URL: expected url", errors)

if __name__ == "__main__":
    unittest.main()
