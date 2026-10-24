
"""
ToolSmith Agent
Coordinates retrieval, generation, validation, and registry storage.

Generated code is validated before it can be saved.
This agent does not directly execute generated tools.
"""

from registry import save_tool
from retriever import retrieve_tools
from tool_generator import generate_tool
from validator import validate_tool


def process_task(task: str) -> dict:
    """Retrieve existing tools or generate, validate, and save a candidate."""

    # 1. Validate the user's task.
    if not isinstance(task, str) or not task.strip():
        return {
            "status": "failed",
            "stage": "input",
            "error": "Task must be a non-empty string.",
        }

    task = task.strip()
    retrieval_warning = None

    # 2. Search for approved tools using semantic retrieval.
    try:
        existing_tools = retrieve_tools(task, top_k=3)
    except Exception as exc:
        existing_tools = []
        retrieval_warning = (
            f"Retrieval unavailable: {type(exc).__name__}: {exc}"
        )

    # Return suggestions for review rather than assuming similarity
    # guarantees that a tool is compatible with the requested task.
    if existing_tools:
        return {
            "status": "existing_tools_found",
            "tools": existing_tools,
            "message": (
                "Approved tool candidates found. Review their "
                "functionality and input/output requirements before reuse."
            ),
            "retrieval_warning": retrieval_warning,
        }

    # 3. Generate a candidate.
    candidate = generate_tool(task)

    if not isinstance(candidate, dict):
        return {
            "status": "failed",
            "stage": "generation",
            "error": "Generator returned an invalid response.",
            "retrieval_warning": retrieval_warning,
        }

    if candidate.get("status") != "success":
        return {
            "status": "failed",
            "stage": "generation",
            "error": candidate.get("error", "Tool generation failed."),
            "retrieval_warning": retrieval_warning,
        }

    # 4. Validate the generated code and its test cases.
    validation = validate_tool(
        candidate.get("code"),
        candidate.get("tests"),
    )

    if (
        not isinstance(validation, dict)
        or validation.get("status") != "success"
        or validation.get("passed") is not True
    ):
        return {
            "status": "validation_failed",
            "stage": "validation",
            "candidate": candidate,
            "validation": validation,
            "message": "Validation failed. Candidate was not saved.",
            "retrieval_warning": retrieval_warning,
        }

    # 5. Save only after successful validation.
    save_result = save_tool(candidate, validation)

    if (
        not isinstance(save_result, dict)
        or save_result.get("status") != "success"
    ):
        return {
            "status": "save_failed",
            "stage": "save",
            "candidate": candidate,
            "validation": validation,
            "save_result": save_result,
            "message": "Validation passed, but saving failed.",
            "retrieval_warning": retrieval_warning,
        }

    # 6. Return the complete result.
    return {
        "status": "success",
        "message": "Tool generated, validated, and saved successfully.",
        "tool": candidate,
        "validation": validation,
        "saved": save_result,
        "retrieval_warning": retrieval_warning,
    }


def main() -> None:
    """Run the interactive command-line interface."""

    task = input("What tool do you want to create? ").strip()
    result = process_task(task)

    print(f"\nStatus: {result.get('status', 'unknown')}")
    print(result.get("message", result.get("error", "")))

    if result.get("retrieval_warning"):
        print("\nRetrieval warning:", result["retrieval_warning"])

    # Show existing tools returned by semantic retrieval.
    for tool in result.get("tools", []):
        print(f"\nTool: {tool.get('name', 'Unknown')}")
        print("Description:", tool.get("description", ""))
        print("Similarity:", tool.get("similarity_score"))

    # Show generated tool details.
    candidate = result.get("candidate") or result.get("tool")

    if candidate:
        print("\nGenerated tool:", candidate.get("tool_name"))
        print("Description:", candidate.get("description", ""))

    # Print generated source when validation fails, to help debug it.
    if result.get("status") == "validation_failed" and candidate:
        print("\n--- Generated source code ---")
        print(candidate.get("code", "No generated code available."))
        print("--- End generated source code ---")

    if result.get("validation") is not None:
        print("\nValidation result:")
        print(result["validation"])

    if result.get("save_result") is not None:
        print("\nSave result:")
        print(result["save_result"])

    if result.get("saved") is not None:
        print("\nSaved tool details:")
        print(result["saved"])


if __name__ == "__main__":
    main()
