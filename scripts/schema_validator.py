import json
import argparse
import sys
from typing import Any, Dict, List, Union, Tuple
from pathlib import Path


def validate_type(data: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(data, str)
    if expected_type == "number":
        return isinstance(data, (int, float)) and not isinstance(data, bool)
    if expected_type == "integer":
        return isinstance(data, int) and not isinstance(data, bool)
    if expected_type == "boolean":
        return isinstance(data, bool)
    if expected_type == "array":
        return isinstance(data, list)
    if expected_type == "object":
        return isinstance(data, dict)
    return True


def validate_schema(data: Any, schema: Dict[str, Any], path: str = "") -> List[str]:
    errors: List[str] = []
    if "type" in schema:
        if not validate_type(data, schema["type"]):
            errors.append(f"Invalid type at '{path}': expected {schema['type']}")
            return errors

    if "enum" in schema:
        if data not in schema["enum"]:
            errors.append(f"Invalid value at '{path}': expected one of {schema['enum']}")

    if isinstance(data, dict):
        if "required" in schema:
            for required_field in schema["required"]:
                if required_field not in data:
                    errors.append(f"Missing required field '{required_field}' at '{path}'")

        if "properties" in schema:
            for key, val_schema in schema["properties"].items():
                if key in data:
                    new_path = f"{path}.{key}" if path else key
                    errors.extend(validate_schema(data[key], val_schema, new_path))

    if isinstance(data, list):
        if "items" in schema:
            for index, item in enumerate(data):
                new_path = f"{path}[{index}]"
                errors.extend(validate_schema(item, schema["items"], new_path))

    return errors


def validate_json_file(data_path: Union[str, Path], schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    with open(data_path, "r", encoding="utf-8") as data_file:
        data = json.load(data_file)

    with open(schema_path, "r", encoding="utf-8") as schema_file:
        schema = json.load(schema_file)

    errors = validate_schema(data, schema)
    return len(errors) == 0, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate JSON against JSON schema.")
    parser.add_argument("data", type=str, help="Path to JSON data file")
    parser.add_argument("schema", type=str, help="Path to JSON schema file")
    args = parser.parse_args()

    is_valid, errors = validate_json_file(args.data, args.schema)
    if is_valid:
        print("Validation successful.")
        sys.exit(0)
    else:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
