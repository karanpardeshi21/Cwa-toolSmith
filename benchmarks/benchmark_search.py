
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import registry
from retriever import retrieve_tools

CASES_FILE = Path(__file__).with_name("tool_search_cases.json")


def reciprocal_rank(ranked_names, expected_name):
    for rank, name in enumerate(ranked_names, start=1):
        if name == expected_name:
            return 1.0 / rank
    return 0.0


def main():
    if not CASES_FILE.exists():
        print(f"Benchmark cases not found: {CASES_FILE}")
        return

    cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))

    if not cases:
        print("No benchmark cases found.")
        return

    # Warm up the semantic model before measuring latency.
    try:
        retrieve_tools("benchmark warmup", top_k=1)
    except Exception as exc:
        print(f"Semantic retrieval could not start: {exc}")
        return

    keyword_hit1 = 0
    semantic_hit1 = 0
    semantic_hit3 = 0

    keyword_rr = []
    semantic_rr = []
    keyword_times = []
    semantic_times = []

    for case in cases:
        query = case["query"]
        expected = case["expected_tool"]

        start = time.perf_counter()
        keyword_result = registry.find_tool_by_task(query)
        keyword_times.append(time.perf_counter() - start)

        keyword_names = (
            [keyword_result["name"]]
            if keyword_result is not None
            else []
        )

        start = time.perf_counter()
        semantic_results = retrieve_tools(query, top_k=3)
        semantic_times.append(time.perf_counter() - start)

        semantic_names = [
            tool["name"] for tool in semantic_results
        ]

        keyword_hit1 += int(expected in keyword_names)
        semantic_hit1 += int(
            bool(semantic_names) and semantic_names[0] == expected
        )
        semantic_hit3 += int(expected in semantic_names)

        keyword_rr.append(reciprocal_rank(keyword_names, expected))
        semantic_rr.append(reciprocal_rank(semantic_names, expected))

        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        print(f"Keyword result: {keyword_names or 'No match'}")
        print(f"Semantic ranking: {semantic_names or 'No match'}")

    count = len(cases)

    print("\n========== BENCHMARK RESULTS ==========")
    print(f"Test cases: {count}")
    print(f"Keyword Hit@1: {keyword_hit1 / count:.2%}")
    print(f"Semantic Hit@1: {semantic_hit1 / count:.2%}")
    print(f"Semantic Hit@3: {semantic_hit3 / count:.2%}")
    print(f"Keyword MRR: {statistics.mean(keyword_rr):.3f}")
    print(f"Semantic MRR: {statistics.mean(semantic_rr):.3f}")
    print(
        f"Keyword average latency: "
        f"{statistics.mean(keyword_times) * 1000:.2f} ms"
    )
    print(
        f"Semantic average latency: "
        f"{statistics.mean(semantic_times) * 1000:.2f} ms"
    )


if __name__ == "__main__":
    main()
