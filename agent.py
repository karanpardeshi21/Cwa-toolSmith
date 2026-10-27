"""ToolSmith agent: retrieve compatible tools or generate and validate one."""

import re

from registry import save_tool
from retriever import retrieve_tools
from tool_generator import generate_tool
from validator import validate_tool


# Capability phrases are intentionally conservative. Unknown requests should
# fall back to generation instead of reusing a tool based on similarity alone.
CAPABILITY_ALIASES = {
    
    "numerical_analysis": (
    "numerical analysis",
    "analyze numerical data",
    "analyze numerical dataset",
    "numerical dataset",
),
    "mean": ("mean", "average", "arithmetic mean"),
    "median": ("median",),
    "mode": ("mode", "most frequent", "most common"),
    "addition": ("addition", "add", "sum", "plus", "add two numbers"),
    "subtraction": ("subtraction", "subtract", "difference", "minus"),
    "multiplication": ("multiplication", "multiply", "product", "times"),
    "division": ("division", "divide", "quotient"),
    "sorting": ("sort", "sorting", "ascending order", "descending order"),
    "deduplication": (
        "deduplicate", "deduplication", "remove duplicates",
        "duplicate removal", "unique rows",
    ),
    "slug_generation": (
        "slugify", "slug generation", "url-friendly slug",
        "url friendly slug",
    ),
    "celsius_fahrenheit": (
        "celsius to fahrenheit", "fahrenheit to celsius",
        "convert celsius", "convert fahrenheit",
    ),
}


def _normalize(text: str) -> str:
    text = text.lower().replace("_", " ")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    normalized_text = f" {_normalize(text)} "
    normalized_phrase = f" {_normalize(phrase)} "
    return normalized_phrase in normalized_text


def _requested_capabilities(task: str) -> set[str]:
    requested = set()
    for capability, aliases in CAPABILITY_ALIASES.items():
        if any(_contains_phrase(task, alias) for alias in aliases):
            requested.add(capability)
    return requested


def _tool_metadata_text(tool: dict) -> str:
    parts = [
        str(tool.get("name", "")),
        str(tool.get("description", "")),
    ]

    for key in ("capabilities", "input_schema", "output_schema"):
        value = tool.get(key, "")
        if isinstance(value, (dict, list, tuple)):
            parts.append(str(value))
        else:
            parts.append(str(value))

    return " ".join(parts)


def _is_compatible(task: str, tool: dict) -> tuple[bool, str]:
    """Conservative phrase-based compatibility gate for known capabilities."""
    if not isinstance(tool, dict):
        return False, "Invalid tool record."

    requested = _requested_capabilities(task)
    if not requested:
        return (
            False,
            "Required capabilities are not recognized by the current "
            "compatibility rules.",
        )

    metadata = _tool_metadata_text(tool)
    missing = [
        capability
        for capability in sorted(requested)
        if not any(
            _contains_phrase(metadata, alias)
            for alias in CAPABILITY_ALIASES[capability]
        )
    ]

    if missing:
        return False, "Missing capability: " + ", ".join(missing)

    return True, "Tool metadata covers all recognized requested capabilities."


def process_task(task: str) -> dict:
    """Reuse a compatible approved tool, otherwise generate and validate."""
    if not isinstance(task, str) or not task.strip():
        return {
            "status": "failed",
            "stage": "input",
            "error": "Task must be a non-empty string.",
        }

    task = task.strip()
    retrieval_warning = None

    try:
        candidates = retrieve_tools(task, top_k=3)
    except Exception as exc:
        candidates = []
        retrieval_warning = (
            f"Retrieval unavailable: {type(exc).__name__}: {exc}"
        )

    compatible_tools = []
    rejected_tools = []

    for tool in candidates:
        compatible, reason = _is_compatible(task, tool)
        if compatible:
            matched = dict(tool)
            matched["compatibility_reason"] = reason
            compatible_tools.append(matched)
        else:
            rejected_tools.append(
                {
                    "name": tool.get("name", "Unknown"),
                    "similarity_score": tool.get("similarity_score"),
                    "reason": reason,
                }
            )

    if compatible_tools:
        return {
            "status": "existing_tools_found",
            "tools": compatible_tools,
            "message": (
                "Compatible approved tool candidates found. Review the "
                "tool's schema before execution."
            ),
            "rejected_tools": rejected_tools,
            "retrieval_warning": retrieval_warning,
        }

    try:
        candidate = generate_tool(task)
    except Exception as exc:
        return {
            "status": "failed",
            "stage": "generation",
            "error": f"Tool generation failed: {type(exc).__name__}: {exc}",
            "rejected_tools": rejected_tools,
            "retrieval_warning": retrieval_warning,
        }

    if not isinstance(candidate, dict):
        return {
            "status": "failed",
            "stage": "generation",
            "error": "Generator returned an invalid response.",
            "rejected_tools": rejected_tools,
            "retrieval_warning": retrieval_warning,
        }

    if candidate.get("status") != "success":
        return {
            "status": "failed",
            "stage": "generation",
            "error": candidate.get("error", "Tool generation failed."),
            "candidate": candidate,
            "rejected_tools": rejected_tools,
            "retrieval_warning": retrieval_warning,
        }

    validation = validate_tool(candidate.get("code"), candidate.get("tests"))

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
            "rejected_tools": rejected_tools,
            "retrieval_warning": retrieval_warning,
        }

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
            "saved": save_result,
            "message": "Validation passed, but saving failed.",
            "rejected_tools": rejected_tools,
            "retrieval_warning": retrieval_warning,
        }

    return {
        "status": "success",
        "message": "Tool generated, validated, and saved successfully.",
        "tool": candidate,
        "validation": validation,
        "saved": save_result,
        "rejected_tools": rejected_tools,
        "retrieval_warning": retrieval_warning,
    }


def main() -> None:
    task = input("What tool do you need? ").strip()
    result = process_task(task)

    print(f"\nStatus: {result.get('status', 'unknown')}")
    print(result.get("message", result.get("error", "")))

    if result.get("retrieval_warning"):
        print("\nRetrieval warning:", result["retrieval_warning"])

    for tool in result.get("tools", []):
        print(f"\nCompatible tool: {tool.get('name', 'Unknown')}")
        print("Description:", tool.get("description", ""))
        print("Similarity:", tool.get("similarity_score"))
        print("Reason:", tool.get("compatibility_reason", ""))

    for tool in result.get("rejected_tools", []):
        print(f"\nRejected tool: {tool.get('name', 'Unknown')}")
        print("Reason:", tool.get("reason", ""))

    candidate = result.get("candidate") or result.get("tool")
    if candidate:
        print(
            "\nCandidate:",
            candidate.get("tool_name", candidate.get("name", "Unknown")),
        )
        print("Description:", candidate.get("description", ""))

    if result.get("validation") is not None:
        print("\nValidation result:")
        print(result["validation"])

    if result.get("saved") is not None:
        print("\nRegistry result:")
        print(result["saved"])


if __name__ == "__main__":
    main()
