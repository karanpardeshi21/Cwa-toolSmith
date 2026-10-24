
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


import registry


class TestLoadRegistry(unittest.TestCase):

    def test_creates_empty_registry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with (
                patch.object(registry, "REGISTRY_DIR", temp_path),
                patch.object(
                    registry,
                    "REGISTRY_FILE",
                    temp_path / "registry.json",
                ),
            ):
                result = registry.load_registry()

                self.assertEqual(result, {"tools": {}})
                self.assertTrue(
                    (temp_path / "registry.json").exists()
                )

    def test_loads_existing_registry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            registry_file = temp_path / "registry.json"

            expected = {"tools": {"csv_cleaner": []}}
            registry_file.write_text(
                json.dumps(expected),
                encoding="utf-8",
            )

            with (
                patch.object(registry, "REGISTRY_DIR", temp_path),
                patch.object(
                    registry, "REGISTRY_FILE", registry_file
                ),
            ):
                result = registry.load_registry()

            self.assertEqual(result, expected)

    def test_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            registry_file = temp_path / "registry.json"
            registry_file.write_text(
                "{invalid json",
                encoding="utf-8",
            )

            with (
                patch.object(registry, "REGISTRY_DIR", temp_path),
                patch.object(
                    registry, "REGISTRY_FILE", registry_file
                ),
            ):
                with self.assertRaises(ValueError):
                    registry.load_registry()


class TestFindTool(unittest.TestCase):

    def test_returns_none_when_tool_missing(self):
        with patch.object(
            registry, "load_registry",
            return_value={"tools": {}},
        ):
            result = registry.find_tool("unknown_tool")

        self.assertIsNone(result)

    def test_returns_latest_approved_version(self):
        tools = {
            "csv_cleaner": [
                {
                    "name": "csv_cleaner",
                    "version": 1,
                    "validation": {"passed": True},
                },
                {
                    "name": "csv_cleaner",
                    "version": 2,
                    "validation": {"passed": False},
                },
                {
                    "name": "csv_cleaner",
                    "version": 3,
                    "validation": {"passed": True},
                },
            ]
        }

        with patch.object(
            registry, "load_registry",
            return_value={"tools": tools},
        ):
            result = registry.find_tool("csv_cleaner")

        self.assertIsNotNone(result)
        self.assertEqual(result["version"], 3)

    def test_returns_none_when_all_versions_failed(self):
        tools = {
            "csv_cleaner": [
                {
                    "name": "csv_cleaner",
                    "version": 1,
                    "validation": {"passed": False},
                }
            ]
        }

        with patch.object(
            registry, "load_registry",
            return_value={"tools": tools},
        ):
            result = registry.find_tool("csv_cleaner")

        self.assertIsNone(result)


class TestFindToolByTask(unittest.TestCase):

    def test_find_tool_by_task_matches_capabilities(self):
        tools = {
            "csv_duplicate_detector": [
                {
                    "name": "csv_duplicate_detector",
                    "version": 1,
                    "description": "Detect duplicate IDs in CSV files",
                    "capabilities": [
                        "csv",
                        "duplicate detection",
                    ],
                    "validation": {"passed": True},
                }
            ]
        }

        with patch.object(
            registry, "load_registry",
            return_value={"tools": tools},
        ):
            result = registry.find_tool_by_task(
                "Find duplicate IDs in CSV"
            )

        self.assertIsNotNone(result)
        self.assertEqual(
            result["name"], "csv_duplicate_detector"
        )

    def test_find_tool_by_task_returns_none_for_empty_task(self):
        self.assertIsNone(registry.find_tool_by_task(""))

    def test_find_tool_by_task_ignores_unapproved_tools(self):
        tools = {
            "csv_duplicate_detector": [
                {
                    "name": "csv_duplicate_detector",
                    "version": 1,
                    "description": "Detect duplicate IDs in CSV files",
                    "capabilities": [
                        "csv",
                        "duplicate detection",
                    ],
                    "validation": {"passed": False},
                }
            ]
        }

        with patch.object(
            registry, "load_registry",
            return_value={"tools": tools},
        ):
            result = registry.find_tool_by_task(
                "Find duplicate IDs in CSV"
            )

        self.assertIsNone(result)


class TestGetToolVersion(unittest.TestCase):

    def test_returns_latest_approved_version(self):
        tool = {
            "name": "csv_cleaner",
            "version": 3,
            "validation": {"passed": True},
        }

        with patch.object(
            registry, "find_tool", return_value=tool
        ):
            result = registry.get_tool_version("csv_cleaner")

        self.assertEqual(result, 3)

    def test_returns_none_when_tool_missing(self):
        with patch.object(
            registry, "find_tool", return_value=None
        ):
            result = registry.get_tool_version("unknown_tool")

        self.assertIsNone(result)

class TestSaveTool(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.registry_dir = self.base_path / "tool_registry"
        self.registry_file = self.registry_dir / "registry.json"

        self.patches = [
            patch.object(registry, "BASE_DIR", self.base_path),
            patch.object(registry, "REGISTRY_DIR", self.registry_dir),
            patch.object(registry, "REGISTRY_FILE", self.registry_file),
        ]

        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self.temp_dir.cleanup()

    def generated_tool(self):
        return {
            "status": "success",
            "tool_name": "csv_cleaner",
            "description": "Clean CSV data",
            "code": "def run(inputs: dict) -> dict:\n    return inputs\n",
            "tests": [],
            "input_schema": {},
            "output_schema": {},
            "capabilities": ["csv", "cleaning"],
            "metadata": {},
        }

    def validation_result(self):
        return {
            "status": "success",
            "passed": True,
            "syntax_valid": True,
            "tests_passed": 1,
            "tests_failed": 0,
            "errors": [],
        }

    def test_saves_validated_tool(self):
        result = registry.save_tool(
            self.generated_tool(),
            self.validation_result(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["version"], 1)

        saved_file = self.base_path / result["code_path"]
        self.assertTrue(saved_file.exists())

        saved_tool = registry.find_tool("csv_cleaner")
        self.assertIsNotNone(saved_tool)
        self.assertEqual(saved_tool["version"], 1)
        self.assertEqual(
            saved_tool["validation"]["syntax_valid"], True
        )
        self.assertEqual(
            saved_tool["validation"]["tests_passed"], 1
        )

    def test_rejects_failed_validation(self):
        validation = self.validation_result()
        validation["status"] = "failed"
        validation["passed"] = False
        validation["errors"] = ["Test failed"]

        result = registry.save_tool(
            self.generated_tool(), validation
        )

        self.assertEqual(result["status"], "failed")
        self.assertIsNone(registry.find_tool("csv_cleaner"))

    def test_increments_version(self):
        first = registry.save_tool(
            self.generated_tool(), self.validation_result()
        )
        second = registry.save_tool(
            self.generated_tool(), self.validation_result()
        )

        self.assertEqual(first["version"], 1)
        self.assertEqual(second["version"], 2)

    def test_rejects_missing_code(self):
        tool = self.generated_tool()
        tool["code"] = ""

        result = registry.save_tool(
            tool, self.validation_result()
        )

        self.assertEqual(result["status"], "failed")
        self.assertIsNone(registry.find_tool("csv_cleaner"))


if __name__ == "__main__":
    unittest.main()
