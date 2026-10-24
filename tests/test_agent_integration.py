
from unittest.mock import patch

import agent


def make_candidate():
    return {
        "status": "success",
        "tool_name": "number_analysis_tool",
        "description": "Analyze a list of numbers.",
        "code": (
            "def run(input_data: dict) -> dict:\n"
            "    return {'total': sum(input_data['numbers'])}\n"
        ),
        "tests": [
            {
                "input": {"numbers": [1, 2, 3]},
                "expected": {"total": 6},
            }
        ],
        "input_schema": {"numbers": "list[int]"},
        "output_schema": {"total": "int"},
        "capabilities": ["number analysis"],
        "metadata": {"generator_version": "test"},
    }


def test_agent_saves_candidate_after_successful_validation():
    candidate = make_candidate()
    validation = {
        "status": "success",
        "passed": True,
        "syntax_valid": True,
        "tests_passed": 1,
        "tests_failed": 0,
        "errors": [],
    }
    saved = {
        "status": "success",
        "tool_name": "number_analysis_tool",
        "version": 1,
    }

    with (
        patch.object(agent, "retrieve_tools", return_value=[]),
        patch.object(agent, "generate_tool", return_value=candidate),
        patch.object(agent, "validate_tool", return_value=validation),
        patch.object(agent, "save_tool", return_value=saved) as save_mock,
    ):
        result = agent.process_task("analyze these numbers")

    assert result["status"] == "success"
    assert result["validation"]["passed"] is True
    save_mock.assert_called_once_with(candidate, validation)


def test_agent_does_not_save_candidate_after_failed_validation():
    candidate = make_candidate()
    validation = {
        "status": "failed",
        "passed": False,
        "syntax_valid": True,
        "tests_passed": 0,
        "tests_failed": 1,
        "errors": ["Output does not match expected result."],
    }

    with (
        patch.object(agent, "retrieve_tools", return_value=[]),
        patch.object(agent, "generate_tool", return_value=candidate),
        patch.object(agent, "validate_tool", return_value=validation),
        patch.object(agent, "save_tool") as save_mock,
    ):
        result = agent.process_task("analyze these numbers")

    assert result["status"] == "validation_failed"
    save_mock.assert_not_called()


def test_agent_returns_existing_tool_candidates_without_generating():
    existing = [{
        "name": "number_analysis_tool",
        "version": 1,
        "description": "Analyze numerical data.",
        "similarity_score": 0.85,
    }]

    with (
        patch.object(agent, "retrieve_tools", return_value=existing),
        patch.object(agent, "generate_tool") as generate_mock,
    ):
        result = agent.process_task("analyze this numerical dataset")

    assert result["status"] == "existing_tools_found"
    assert result["tools"] == existing
    generate_mock.assert_not_called()


def test_agent_rejects_empty_task():
    result = agent.process_task("   ")

    assert result["status"] == "failed"
    assert result["stage"] == "input"
