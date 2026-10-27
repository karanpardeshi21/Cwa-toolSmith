"""Semantic retrieval for approved ToolSmith tools."""

import json
import math
from functools import lru_cache
from typing import Any

import registry

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_model():
    """Load the embedding model once per process."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency. Install it with: "
            "python3 -m pip install sentence-transformers"
        ) from exc

    return SentenceTransformer(MODEL_NAME)


def _is_approved_record(tool: Any) -> bool:
    """Check whether a registry record is approved and versioned."""
    return (
        isinstance(tool, dict)
        and isinstance(tool.get("name"), str)
        and isinstance(tool.get("version"), int)
        and not isinstance(tool.get("version"), bool)
        and tool["version"] > 0
        and isinstance(tool.get("validation"), dict)
        and tool["validation"].get("passed") is True
    )


def _latest_approved_tools() -> list[dict]:
    """Return the latest approved version of each registered tool."""
    registry_data = registry.load_registry()
    if not isinstance(registry_data, dict):
        return []

    tools_by_name = registry_data.get("tools", {})
    if not isinstance(tools_by_name, dict):
        return []

    approved_tools = []

    for name, versions in tools_by_name.items():
        if not isinstance(versions, list):
            continue

        candidates = [
            tool
            for tool in versions
            if _is_approved_record(tool) and tool.get("name") == name
        ]

        if candidates:
            approved_tools.append(
                max(candidates, key=lambda item: item["version"])
            )

    return approved_tools


def _tool_document(tool: dict) -> str:
    """Build searchable text from descriptive metadata and schemas."""
    capabilities = tool.get("capabilities", [])
    if not isinstance(capabilities, list):
        capabilities = []

    return "\n".join(
        [
            f"Tool name: {tool.get('name', '')}",
            f"Description: {tool.get('description', '')}",
            "Capabilities: " + ", ".join(map(str, capabilities)),
            "Input schema: " + json.dumps(
                tool.get("input_schema", {}), sort_keys=True, default=str
            ),
            "Output schema: " + json.dumps(
                tool.get("output_schema", {}), sort_keys=True, default=str
            ),
        ]
    )


def _cosine_similarity(vector_a, vector_b) -> float:
    """Calculate cosine similarity between two vectors."""
    a = [float(value) for value in vector_a]
    b = [float(value) for value in vector_b]

    if len(a) != len(b) or not a:
        return 0.0

    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def retrieve_tools(
    query: str,
    top_k: int = 3,
    min_score: float | None = None,
) -> list[dict]:
    """
    Return approved tools ranked by semantic similarity.

    Scores rank candidates; they do not prove functional compatibility.
    """
    if not isinstance(query, str) or not query.strip():
        return []

    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    if min_score is not None:
        if (
            isinstance(min_score, bool)
            or not isinstance(min_score, (int, float))
            or not math.isfinite(min_score)
            or not -1.0 <= min_score <= 1.0
        ):
            raise ValueError("min_score must be between -1 and 1.")

    tools = _latest_approved_tools()
    if not tools:
        return []

    model = _load_model()
    documents = [_tool_document(tool) for tool in tools]
    embeddings = model.encode(
        [query.strip(), *documents],
        normalize_embeddings=True,
    )

    query_embedding = embeddings[0]
    ranked = []

    for tool, embedding in zip(tools, embeddings[1:]):
        score = _cosine_similarity(query_embedding, embedding)

        if min_score is not None and score < min_score:
            continue

        result = dict(tool)
        result["similarity_score"] = round(score, 6)
        ranked.append(result)

    ranked.sort(
        key=lambda item: (
            item["similarity_score"],
            item["version"],
            item["name"],
        ),
        reverse=True,
    )
    return ranked[:top_k]
