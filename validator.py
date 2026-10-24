
"""Validation utilities for ToolSmith-generated Python tools."""

import ast
import json
import math
import subprocess
import sys


def check_syntax(code: str) -> dict:
    """Check whether generated code has valid Python syntax."""
    if not isinstance(code, str) or not code.strip():
        return {"valid": False, "error": "Code must be a non-empty string."}

    try:
        ast.parse(code)
        return {"valid": True, "error": None}
    except SyntaxError as exc:
        return {
            "valid": False,
            "error": f"Line {exc.lineno}: {exc.msg}",
        }


def check_entry_point(code: str) -> dict:
    """Check that code defines a regular run(input_data) function."""
    syntax_result = check_syntax(code)

    if not syntax_result["valid"]:
        return {
            "valid": False,
            "error": f"Invalid Python syntax: {syntax_result['error']}",
        }

    tree = ast.parse(code)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            positional_args = node.args.posonlyargs + node.args.args

            if len(positional_args) != 1 or node.args.vararg is not None:
                return {
                    "valid": False,
                    "error": "run() must accept exactly one positional argument: input_data.",
                }

            if node.args.kwonlyargs:
                return {
                    "valid": False,
                    "error": "run() must not require keyword-only arguments.",
                }

            if node.args.kwarg is not None:
                return {
                    "valid": False,
                    "error": "run() must not accept arbitrary keyword arguments.",
                }

            if positional_args[0].arg != "input_data":
                return {
                    "valid": False,
                    "error": "The run() parameter must be named input_data.",
                }

            if node.returns is not None:
                if not (
                    isinstance(node.returns, ast.Name)
                    and node.returns.id == "dict"
                ):
                    return {
                        "valid": False,
                        "error": "run() return annotation must be dict if specified.",
                    }

            return {"valid": True, "error": None}

        # Reject async run() definitions at module level.
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "run":
            return {
                "valid": False,
                "error": "run() must be a regular function, not async.",
            }

    return {
        "valid": False,
        "error": "Generated code must define run(input_data: dict) -> dict.",
    }


def run_test_case(code: str, test_case: dict, timeout: int = 5) -> dict:
    """Execute one test case in a subprocess and compare dictionary output."""
    if not isinstance(test_case, dict):
        return {"passed": False, "error": "Test case must be a dictionary."}

    if not isinstance(test_case.get("input"), dict):
        return {
            "passed": False,
            "error": "Test case must contain an input dictionary.",
        }

    if not isinstance(test_case.get("expected"), dict):
        return {
            "passed": False,
            "error": "Test case must contain an expected dictionary.",
        }

    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        return {
            "passed": False,
            "error": "Timeout must be a positive finite number.",
        }

    runner = r'''
import json
import sys

payload = json.loads(sys.stdin.read())
code = payload["code"]
test_case = payload["test_case"]

namespace = {"__name__": "generated_tool"}
exec(compile(code, "<generated_tool>", "exec"), namespace)

run = namespace.get("run")
if not callable(run):
    raise ValueError("Generated code must define a callable run() function.")

result = run(test_case["input"])

if not isinstance(result, dict):
    raise TypeError("run() must return a dictionary.")

print(json.dumps(result))
'''

    payload = json.dumps({
        "code": code,
        "test_case": test_case,
    })

    try:
        process = subprocess.run(
            [sys.executable, "-I", "-c", runner],
            input=payload,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "error": f"Test timed out after {timeout} seconds.",
        }
    except OSError as exc:
        return {
            "passed": False,
            "error": f"Could not start test subprocess: {exc}",
        }

    if process.returncode != 0:
        return {
            "passed": False,
            "error": process.stderr.strip() or "Tool execution failed.",
        }

    try:
        # The last line is the runner's JSON result. This also tolerates
        # ordinary print() calls made by the generated function.
        output_lines = process.stdout.strip().splitlines()
        actual = json.loads(output_lines[-1])
    except (json.JSONDecodeError, IndexError):
        return {
            "passed": False,
            "error": "Tool did not produce a valid JSON dictionary.",
        }

    if not isinstance(actual, dict):
        return {
            "passed": False,
            "actual": actual,
            "expected": test_case["expected"],
            "error": "Tool output must be a dictionary.",
        }

    expected = test_case["expected"]

    if actual == expected:
        return {
            "passed": True,
            "actual": actual,
            "expected": expected,
            "error": None,
        }

    return {
        "passed": False,
        "actual": actual,
        "expected": expected,
        "error": "Output does not match expected result.",
    }


def validate_tool(code: str, tests: list) -> dict:
    """Validate syntax, entry point, and all generated tool test cases."""
    result = {
        "status": "failed",
        "passed": False,
        "syntax_valid": False,
        "tests_passed": 0,
        "tests_failed": 0,
        "errors": [],
    }

    syntax_result = check_syntax(code)
    result["syntax_valid"] = syntax_result["valid"]

    if not syntax_result["valid"]:
        result["errors"].append(syntax_result["error"])
        return result

    entry_result = check_entry_point(code)

    if not entry_result["valid"]:
        result["errors"].append(entry_result["error"])
        return result

    if not isinstance(tests, list):
        result["errors"].append("Tests must be provided as a list.")
        return result

    if not tests:
        result["errors"].append("At least one test case is required.")
        return result

    for index, test_case in enumerate(tests):
        test_result = run_test_case(code, test_case)

        if test_result["passed"]:
            result["tests_passed"] += 1
        else:
            result["tests_failed"] += 1
            result["errors"].append(
                f"Test {index + 1}: {test_result['error']}"
            )

    result["passed"] = (
        result["tests_failed"] == 0
        and result["tests_passed"] == len(tests)
    )
    result["status"] = "success" if result["passed"] else "failed"

    return result
