
import json
import re
from datetime import datetime, timezone
from typing import Any, Callable
from groq_client import generate_with_groq


def _make_tool_name(task: str) -> str:
    """Convert a task description into a readable tool name."""
    words = re.findall(r"[a-zA-Z0-9]+", task.lower())
    name = "_".join(words[:5])
    return f"{name or 'generated'}_tool"


def _build_prompt(task: str) -> str:
    """Create the instructions sent to the configured LLM."""
    return f"""
You are a Python tool-generation component for ToolSmith.

Create a Python tool for this task:
{task}

Return ONLY a valid JSON object with these keys:
- description: string
- code: string containing Python source code
- tests: list of test-case dictionaries
- input_schema: dictionary
- output_schema: dictionary
- capabilities: list of strings

Requirements:
1. The generated source must define run(inputs: dict) -> dict.
2. Do not include API calls, file-system access, shell commands,
   network access, or dynamic code execution unless explicitly
   approved by the application's safety policy.
3. Keep the implementation focused on the requested task.
4. Tests must use this exact structure:
   {{"input": {{"ids": [1, 2, 2, 3]}},
     "expected": {{"duplicates": [2]}}}}
5. Expected outputs must describe the intended behavior independently
   of executing the generated code.
6. Include at least two meaningful test cases where practical.
7. Do not claim that tests passed. Testing is handled separately.
8. Return JSON only, without Markdown fences.
""".strip()


def generate_tool(
    task: str,
    llm_generate: Callable[[str], Any] = generate_with_groq,
) -> dict:
    """
    Ask a configured LLM to generate a tool candidate.

    llm_generate is a provider adapter supplied by the application.
    This function does not validate or execute the generated code.
    """
    if not isinstance(task, str) or not task.strip():
        return {
            "status": "failed",
            "error": "Task must be a non-empty string."
        }

    if not callable(llm_generate):
        return {
            "status": "failed",
            "error": "A configured LLM generation function is required."
        }

    clean_task = task.strip()

    try:
        response = llm_generate(_build_prompt(clean_task))

        if isinstance(response, dict):
            candidate = response
        elif isinstance(response, str):
            # Accept plain JSON only; do not execute model output.
            candidate = json.loads(response)
        else:
            raise ValueError("LLM response must be a JSON string or dictionary.")

        required = {
            "description",
            "code",
            "tests",
            "input_schema",
            "output_schema",
            "capabilities",
        }

        missing = required - candidate.keys()
        if missing:
            raise ValueError(
                f"Generated response is missing fields: {sorted(missing)}"
            )

        if not isinstance(candidate["code"], str) or not candidate["code"].strip():
            raise ValueError("Generated code must be a non-empty string.")

        if not isinstance(candidate["tests"], list):
            raise ValueError("Generated tests must be a list.")

        for test in candidate["tests"]:
            if (
                not isinstance(test, dict)
                or "input" not in test
                or "expected" not in test
                or not isinstance(test["input"], dict)
                or not isinstance(test["expected"], dict)
            ):
                raise ValueError(
                    "Each test must contain dictionary fields: input and expected."
                )

        return {
            "status": "success",
            "tool_name": _make_tool_name(clean_task),
            "description": candidate["description"],
            "code": candidate["code"],
            "tests": candidate["tests"],
            "input_schema": candidate["input_schema"],
            "output_schema": candidate["output_schema"],
            "capabilities": candidate["capabilities"],
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "generator_version": "0.2.0",
                "generation_mode": "llm_candidate",
            },
        }

    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return {
            "status": "failed",
            "error": f"Invalid tool-generation response: {exc}",
        }
    except Exception as exc:
        # Avoid exposing provider credentials or internal tracebacks.
        return {
            "status": "failed",
            "error": f"Tool generation failed: {type(exc).__name__}",
        }
