
"""Execute approved ToolSmith tools in a subprocess."""

import json
import subprocess
import sys
from pathlib import Path

from registry import find_tool


DEFAULT_TIMEOUT = 5
MAX_TIMEOUT = 10


def execute_tool(
    name: str,
    input_data: dict,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Execute the latest approved version of a registered tool."""

    # 1. Validate request.
    if not isinstance(name, str) or not name.strip():
        return {
            "status": "failed",
            "stage": "input",
            "error": "Tool name must be a non-empty string.",
        }

    if not isinstance(input_data, dict):
        return {
            "status": "failed",
            "stage": "input",
            "error": "input_data must be a dictionary.",
        }

    if (
        not isinstance(timeout, int)
        or isinstance(timeout, bool)
        or not 0 < timeout <= MAX_TIMEOUT
    ):
        return {
            "status": "failed",
            "stage": "input",
            "error": (
                f"timeout must be an integer between 1 and "
                f"{MAX_TIMEOUT} seconds."
            ),
        }

    # 2. Find the latest approved tool.
    tool_name = name.strip()
    tool = find_tool(tool_name)

    if tool is None:
        return {
            "status": "failed",
            "stage": "lookup",
            "error": f"No approved tool found with name '{tool_name}'.",
        }

    # 3. Verify source path is inside tools/generated.
    code_path_value = tool.get("code_path")

    if not isinstance(code_path_value, str) or not code_path_value.strip():
        return {
            "status": "failed",
            "stage": "lookup",
            "error": "Approved tool has no valid code path.",
        }

    project_root = Path(__file__).resolve().parent
    tools_root = (project_root / "tools" / "generated").resolve()
    code_path = (project_root / code_path_value).resolve()

    try:
        code_path.relative_to(tools_root)
    except ValueError:
        return {
            "status": "failed",
            "stage": "lookup",
            "error": "Tool code path is outside the generated-tools directory.",
        }

    if not code_path.is_file() or code_path.suffix != ".py":
        return {
            "status": "failed",
            "stage": "lookup",
            "error": "Tool source file does not exist or is not a Python file.",
        }

    # 4. Execute the tool in a separate Python process.
    # Note: this is process isolation, NOT a security sandbox.
    runner = r'''
import json
import sys

source_path = sys.argv[1]

try:
    with open(source_path, "r", encoding="utf-8") as source_file:
        code = source_file.read()

    namespace = {"__name__": "generated_tool"}
    exec(compile(code, source_path, "exec"), namespace)

    run = namespace.get("run")
    if not callable(run):
        raise ValueError("Tool must define a callable run(input_data).")

    input_data = json.load(sys.stdin)
    result = run(input_data)

    if not isinstance(result, dict):
        raise TypeError("Tool must return a dictionary.")

    response = {"status": "success", "output": result}

except Exception as exc:
    response = {
        "status": "failed",
        "error": f"{type(exc).__name__}: {exc}",
    }

try:
    print(json.dumps(response, allow_nan=False))
except (TypeError, ValueError) as exc:
    print(json.dumps({
        "status": "failed",
        "error": f"Output is not JSON serializable: {type(exc).__name__}",
    }))
    sys.exit(1)

if response["status"] != "success":
    sys.exit(1)
'''

    # 5. Run with a bounded timeout and output size.
    try:
        process = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                runner,
                str(code_path),
            ],
            input=json.dumps(input_data, allow_nan=False),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=str(project_root),
        )

    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "stage": "execution",
            "error": f"Tool exceeded the {timeout}-second timeout.",
        }

    except (OSError, TypeError, ValueError) as exc:
        return {
            "status": "failed",
            "stage": "execution",
            "error": f"Could not start tool process: {type(exc).__name__}: {exc}",
        }

    # 6. Reject unexpectedly large captured output.
    # subprocess.run captures output before this check, so this is
    # a response-size check, NOT a hard memory limit.
    max_output_chars = 1_000_000

    if len(process.stdout) > max_output_chars:
        return {
            "status": "failed",
            "stage": "execution",
            "error": "Tool output exceeded the allowed response size.",
        }

    # 7. Parse the runner's JSON response.
    try:
        response = json.loads(process.stdout)
    except (json.JSONDecodeError, TypeError):
        return {
            "status": "failed",
            "stage": "execution",
            "error": "Tool returned an invalid response.",
        }

    if not isinstance(response, dict):
        return {
            "status": "failed",
            "stage": "execution",
            "error": "Tool returned an invalid response structure.",
        }

    if process.returncode != 0 or response.get("status") != "success":
        return {
            "status": "failed",
            "stage": "execution",
            "error": response.get("error", "Tool execution failed."),
        }

    # 8. Return structured result.
    return {
        "status": "success",
        "tool_name": tool.get("name", tool_name),
        "version": tool.get("version"),
        "output": response["output"],
    }
