import unittest
import sys
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from schema_validator import validate_type, validate_schema, validate_json_file


class TestSchemaValidator(unittest.TestCase):

    def test_validate_type_string(self) -> None:
        self.assertTrue(validate_type("hello", "string"))
        self.assertFalse(validate_type(123, "string"))
        self.assertFalse(validate_type(True, "string"))

    def test_validate_type_number_integer(self) -> None:
        self.assertTrue(validate_type(123, "number"))
        self.assertTrue(validate_type(123.45, "number"))
        self.assertFalse(validate_type(True, "number"))

        self.assertTrue(validate_type(123, "integer"))
        self.assertFalse(validate_type(123.45, "integer"))

    def test_validate_type_boolean(self) -> None:
        self.assertTrue(validate_type(True, "boolean"))
        self.assertTrue(validate_type(False, "boolean"))
        self.assertFalse(validate_type(1, "boolean"))
        self.assertFalse(validate_type("true", "boolean"))

    def test_validate_type_array(self) -> None:
        self.assertTrue(validate_type([1, 2, 3], "array"))
        self.assertFalse(validate_type({"a": 1}, "array"))

    def test_validate_type_object(self) -> None:
        self.assertTrue(validate_type({"a": 1}, "object"))
        self.assertFalse(validate_type([1, 2, 3], "object"))

    def test_validate_schema_type(self) -> None:
        schema: Dict[str, Any] = {"type": "string"}
        self.assertEqual(validate_schema("test", schema), [])

        errors = validate_schema(123, schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("Invalid type", errors[0])

    def test_validate_schema_enum(self) -> None:
        schema: Dict[str, Any] = {"enum": ["red", "green", "blue"]}
        self.assertEqual(validate_schema("red", schema), [])

        errors = validate_schema("yellow", schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("Invalid value", errors[0])

    def test_validate_schema_required(self) -> None:
        schema: Dict[str, Any] = {
            "type": "object",
            "required": ["name", "age"]
        }
        valid_data: Dict[str, Any] = {"name": "Alice", "age": 30}
        self.assertEqual(validate_schema(valid_data, schema), [])

        invalid_data: Dict[str, Any] = {"name": "Alice"}
        errors = validate_schema(invalid_data, schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("Missing required field", errors[0])

    def test_validate_schema_nested_properties(self) -> None:
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer"}
                    }
                }
            }
        }
        valid_data: Dict[str, Any] = {"user": {"age": 25}}
        self.assertEqual(validate_schema(valid_data, schema), [])

        invalid_data: Dict[str, Any] = {"user": {"age": "25"}}
        errors = validate_schema(invalid_data, schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("user.age", errors[0])

    def test_validate_schema_nested_array(self) -> None:
        schema: Dict[str, Any] = {
            "type": "array",
            "items": {"type": "string"}
        }
        valid_data: List[Any] = ["a", "b", "c"]
        self.assertEqual(validate_schema(valid_data, schema), [])

        invalid_data: List[Any] = ["a", 1, "c"]
        errors = validate_schema(invalid_data, schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("[1]", errors[0])

    def test_validate_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir).resolve()

            data_file = dir_path / "data.json"
            schema_file = dir_path / "schema.json"

            with open(data_file, "w", encoding="utf-8") as df:
                json.dump({"name": "Bob"}, df)

            with open(schema_file, "w", encoding="utf-8") as sf:
                json.dump({"type": "object", "required": ["name"]}, sf)

            is_valid, errors = validate_json_file(data_file, schema_file)
            self.assertTrue(is_valid)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
