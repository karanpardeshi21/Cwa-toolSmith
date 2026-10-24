
from unittest.mock import patch

from executor import execute_tool


def test_rejects_empty_tool_name():
    result = execute_tool("", {})
    assert result["status"] == "failed"
    assert result["stage"] == "input"


def test_rejects_non_dictionary_input():
    result = execute_tool("example_tool", [])
    assert result["status"] == "failed"
    assert result["stage"] == "input"


def test_rejects_invalid_timeout():
    result = execute_tool("example_tool", {}, timeout=0)
    assert result["status"] == "failed"
    assert result["stage"] == "input"


def test_rejects_unapproved_tool():
    with patch("executor.find_tool", return_value=None):
        result = execute_tool("missing_tool", {})

    assert result["status"] == "failed"
    assert result["stage"] == "lookup"
    assert "No approved tool" in result["error"]


from pathlib import Path
import json
import tempfile


def test_executes_approved_tool():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        generated_dir = root / "tools" / "generated" / "example_tool"
        generated_dir.mkdir(parents=True)

        code_path = generated_dir / "v1.py"
        code_path.write_text(
            "def run(input_data: dict) -> dict:\n"
            "    return {'total': sum(input_data['numbers'])}\n",
            encoding="utf-8",
        )

        record = {
            "name": "example_tool",
            "version": 1,
            "code_path": "tools/generated/example_tool/v1.py",
            "validation": {"passed": True},
        }

        # Patch paths so the test uses a temporary tool file.
        with (
            patch("executor.find_tool", return_value=record),
            patch("executor.__file__", str(root / "executor.py")),
        ):
            result = execute_tool(
                "example_tool",
                {"numbers": [1, 2, 3]},
            )

    assert result["status"] == "success"
    assert result["output"] == {"total": 6}
    assert result["version"] == 1


def test_handles_missing_tool_source():
    record = {
        "name": "example_tool",
        "version": 1,
        "code_path": "tools/generated/example_tool/v1.py",
        "validation": {"passed": True},
    }

    with patch("executor.find_tool", return_value=record):
        result = execute_tool("example_tool", {})

    assert result["status"] == "failed"
    assert result["stage"] == "lookup"



def test_stops_tool_that_exceeds_timeout():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        generated_dir = root / "tools" / "generated" / "slow_tool"
        generated_dir.mkdir(parents=True)

        code_path = generated_dir / "v1.py"
        code_path.write_text(
            "def run(input_data: dict) -> dict:\n"
            "    while True:\n"
            "        pass\n",
            encoding="utf-8",
        )

        record = {
            "name": "slow_tool",
            "version": 1,
            "code_path": "tools/generated/slow_tool/v1.py",
            "validation": {"passed": True},
        }

        with (
            patch("executor.find_tool", return_value=record),
            patch("executor.__file__", str(root / "executor.py")),
        ):
            result = execute_tool("slow_tool", {}, timeout=1)

    assert result["status"] == "failed"
    assert result["stage"] == "execution"
    assert "timeout" in result["error"].lower()


def test_rejects_timeout_above_maximum():
    result = execute_tool("example_tool", {}, timeout=11)

    assert result["status"] == "failed"
    assert result["stage"] == "input"
    assert "timeout" in result["error"].lower()

