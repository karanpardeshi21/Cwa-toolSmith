
import json
from pathlib import Path
from typing import Any
import re
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parent
REGISTRY_DIR = BASE_DIR / "tool_registry"
REGISTRY_FILE = REGISTRY_DIR / "registry.json"


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



def save_tool(
    generated_tool: dict,
    validation_result: dict,
) -> dict:
    """
    Save a generated tool and register it only after validation
    succeeds and its Python file has been stored successfully.
    """

    # 1. Check generation and validation results.
    if not isinstance(generated_tool, dict):
        return {
            "status": "failed",
            "error": "Invalid generated tool.",
        }

    if generated_tool.get("status") != "success":
        return {
            "status": "failed",
            "error": "Tool generation did not succeed.",
        }

    if not isinstance(validation_result, dict):
        return {
            "status": "failed",
            "error": "Invalid validation result.",
        }

    if (
        validation_result.get("status") != "success"
        or validation_result.get("passed") is not True
    ):
        return {
            "status": "failed",
            "error": "Tool validation failed. Tool was not saved.",
        }

    # 2. Validate the tool name and Python code.
    name = generated_tool.get("tool_name")
    code = generated_tool.get("code")

    if not isinstance(name, str) or not re.fullmatch(
        r"[a-zA-Z][a-zA-Z0-9_]{0,63}", name
    ):
        return {
            "status": "failed",
            "error": "Invalid tool name.",
        }

    if not isinstance(code, str) or not code.strip():
        return {
            "status": "failed",
            "error": "Tool code is missing or empty.",
        }

    # 3. Validate the generated metadata.
    description = generated_tool.get("description", "")
    input_schema = generated_tool.get("input_schema", {})
    output_schema = generated_tool.get("output_schema", {})
    capabilities = generated_tool.get("capabilities", [])
    metadata = generated_tool.get("metadata", {})

    if not isinstance(description, str):
        return {"status": "failed", "error": "Invalid description."}

    if not isinstance(input_schema, dict):
        return {"status": "failed", "error": "Invalid input schema."}

    if not isinstance(output_schema, dict):
        return {"status": "failed", "error": "Invalid output schema."}

    if not isinstance(capabilities, list):
        return {"status": "failed", "error": "Invalid capabilities."}

    if not isinstance(metadata, dict):
        return {"status": "failed", "error": "Invalid metadata."}

    # 4. Prepare versioned storage and the registry record.
    code_file = None
    temp_code_file = None
    temp_registry_file = REGISTRY_FILE.with_suffix(".json.tmp")

    try:
        registry_data = load_registry()
        versions = registry_data["tools"].get(name, [])

        if not isinstance(versions, list):
            return {
                "status": "failed",
                "error": "Invalid tool version records.",
            }

        valid_versions = [
            item["version"]
            for item in versions
            if isinstance(item, dict)
            and isinstance(item.get("version"), int)
            and not isinstance(item.get("version"), bool)
            and item["version"] > 0
        ]

        version = max(valid_versions, default=0) + 1

        tool_dir = BASE_DIR / "tools" / "generated" / name
        tool_dir.mkdir(parents=True, exist_ok=True)

        code_file = tool_dir / f"v{version}.py"
        temp_code_file = tool_dir / f"v{version}.py.tmp"

        if code_file.exists():
            return {
                "status": "failed",
                "error": "Version file already exists.",
            }

        # 5. Write the candidate code to a temporary file.
        temp_code_file.write_text(code, encoding="utf-8")

        # Publish the versioned code file.
        temp_code_file.replace(code_file)
        temp_code_file = None

        # Preserve the complete validation result.
        record = {
            "name": name,
            "version": version,
            "description": description,
            "code_path": code_file.relative_to(BASE_DIR).as_posix(),
            "input_schema": input_schema,
            "output_schema": output_schema,
            "capabilities": capabilities,
            "metadata": metadata,
            "validation": dict(validation_result),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # 6. Prepare the updated registry.
        updated_registry = dict(registry_data)
        updated_tools = dict(registry_data["tools"])
        updated_tools[name] = [*versions, record]
        updated_registry["tools"] = updated_tools

        REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

        # Write the new registry, then replace the old file.
        temp_registry_file.write_text(
            json.dumps(updated_registry, indent=2),
            encoding="utf-8",
        )
        temp_registry_file.replace(REGISTRY_FILE)

        return {
            "status": "success",
            "tool_name": name,
            "version": version,
            "code_path": record["code_path"],
        }

    except (OSError, ValueError, TypeError, KeyError) as exc:
        # Avoid leaving an unregistered code file after a failure.
        if code_file is not None:
            try:
                code_file.unlink(missing_ok=True)
            except OSError:
                pass

        return {
            "status": "failed",
            "error": f"Could not save tool: {exc}",
        }

    finally:
        if temp_code_file is not None:
            temp_code_file.unlink(missing_ok=True)


