
import json
from pathlib import Path
from typing import Any


# --------------------------------------------------
# Registry paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
REGISTRY_DIR = BASE_DIR / "tool_registry"
REGISTRY_FILE = REGISTRY_DIR / "registry.json"


# --------------------------------------------------
# 1. Load registry
# --------------------------------------------------

def load_registry() -> dict[str, Any]:
    """
    Load tool metadata from registry.json.

    If the registry does not exist, initialize an empty registry.
    Raise an error if the existing registry contains invalid JSON
    or an unsupported structure.
    """
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

    if not REGISTRY_FILE.exists():
        registry = {"tools": {}}

        REGISTRY_FILE.write_text(
            json.dumps(registry, indent=2),
            encoding="utf-8",
        )

        return registry

    try:
        registry = json.loads(
            REGISTRY_FILE.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Registry JSON is invalid: {REGISTRY_FILE}"
        ) from exc

    if not isinstance(registry, dict):
        raise ValueError("Registry must be a JSON object.")

    if not isinstance(registry.get("tools"), dict):
        raise ValueError(
            "Registry must contain a 'tools' object."
        )

    return registry


# --------------------------------------------------
# 2. Find tool by exact name
# --------------------------------------------------

def find_tool(name: str) -> dict | None:
    """
    Find an approved tool by its exact name.

    Returns the highest approved version's metadata,
    or None if no approved version exists.
    """
    registry = load_registry()

    tool_versions = registry["tools"].get(name)

    if not isinstance(tool_versions, list):
        return None

    approved_versions = [
        tool
        for tool in tool_versions
        if isinstance(tool, dict)
        and isinstance(tool.get("validation"), dict)
        and tool["validation"].get("passed") is True
        and isinstance(tool.get("version"), int)
        and not isinstance(tool.get("version"), bool)
    ]

    if not approved_versions:
        return None

    return max(
        approved_versions,
        key=lambda tool: tool["version"],
    )
    

def find_tool_by_task(task: str) -> dict | None:
    """
    Find an approved tool using simple keyword matching.

    Searches tool names, descriptions, and capabilities.
    Returns the highest-version approved candidate with
    the best keyword overlap, or None if no candidate matches.

    This is a basic discovery heuristic, not semantic matching.
    The agent must verify schema and capability compatibility.
    """
    if not isinstance(task, str) or not task.strip():
        return None

    registry = load_registry()
    task_words = set(task.lower().split())

    best_tool = None
    best_score = 0

    for name, versions in registry["tools"].items():
        if not isinstance(versions, list):
            continue

        approved_versions = [
            tool
            for tool in versions
            if isinstance(tool, dict)
            and isinstance(tool.get("validation"), dict)
            and tool["validation"].get("passed") is True
            and isinstance(tool.get("version"), int)
            and not isinstance(tool.get("version"), bool)
        ]

        if not approved_versions:
            continue

        latest_tool = max(
            approved_versions,
            key=lambda tool: tool["version"],
        )

        searchable_text = " ".join([
            name,
            str(latest_tool.get("description", "")),
            " ".join(
                str(capability)
                for capability in latest_tool.get("capabilities", [])
            ) if isinstance(latest_tool.get("capabilities", []), list)
            else "",
        ]).lower()

        searchable_words = set(searchable_text.split())
        score = len(task_words & searchable_words)

        if score > best_score:
            best_score = score
            best_tool = latest_tool

    return best_tool

def get_tool_version(name: str) -> int | None:
    """Return the latest approved version number for a tool."""
    tool = find_tool(name)

    if tool is None:
        return None

    return tool["version"]

