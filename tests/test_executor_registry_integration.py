
from unittest.mock import patch

from executor import execute_tool


def test_executor_uses_registry_approved_tool():
    approved_tool = {
        "name": "number_analysis_tool",
        "version": 1,
        "code_path": "tools/generated/number_analysis_tool/v1.py",
        "validation": {"passed": True},
    }

    with patch(
        "executor.find_tool",
        return_value=approved_tool,
    ) as find_mock:
        # The source file isn't present in this test, so lookup
        # should stop safely before attempting execution.
        result = execute_tool("number_analysis_tool", {"numbers": [1, 2, 3]})

    find_mock.assert_called_once_with("number_analysis_tool")
    assert result["status"] == "failed"
    assert result["stage"] == "lookup"
