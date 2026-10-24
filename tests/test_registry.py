
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


if __name__ == "__main__":
    unittest.main()
