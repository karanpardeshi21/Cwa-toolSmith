
import unittest
from unittest.mock import patch

import retriever


def approved_tool(
    name,
    description,
    version=1,
    passed=True,
    capabilities=None,
    input_schema=None,
    output_schema=None,
):
    """Create a sample tool record for testing."""
    return {
        "name": name,
        "version": version,
        "description": description,
        "capabilities": capabilities or [],
        "input_schema": input_schema or {},
        "output_schema": output_schema or {},
        "validation": {
            "status": "success" if passed else "failed",
            "passed": passed,
        },
    }


class FakeEmbeddingModel:
    """Deterministic fake model; no real model download is required."""

    def encode(self, texts, normalize_embeddings=True):
        vectors = []

        for text in texts:
            text = text.lower()

            if "query_duplicate" in text:
                vectors.append([1.0, 0.0])

            elif "duplicate_detector" in text:
                vectors.append([0.9, 0.1])

            elif "weather_tool" in text:
                vectors.append([0.0, 1.0])

            else:
                vectors.append([0.1, 0.9])

        return vectors


class TestRetriever(unittest.TestCase):

    def setUp(self):
        self.tools = {
            "duplicate_detector": [
                approved_tool(
                    "duplicate_detector",
                    "Detect duplicate customer records",
                    version=1,
                    capabilities=["duplicate detection"],
                ),
                approved_tool(
                    "duplicate_detector",
                    "Detect duplicate customer records",
                    version=2,
                    capabilities=["duplicate detection"],
                ),
                approved_tool(
                    "duplicate_detector",
                    "Unapproved duplicate detector",
                    version=3,
                    passed=False,
                ),
            ],
            "weather_tool": [
                approved_tool(
                    "weather_tool",
                    "Retrieve weather forecasts",
                    capabilities=["weather", "forecast"],
                )
            ],
            "failed_tool": [
                approved_tool(
                    "failed_tool",
                    "Find duplicate records",
                    passed=False,
                )
            ],
        }

        self.registry_patch = patch.object(
            retriever.registry,
            "load_registry",
            return_value={"tools": self.tools},
        )
        self.registry_patch.start()
        self.addCleanup(self.registry_patch.stop)

        self.model_patch = patch.object(
            retriever,
            "_load_model",
            return_value=FakeEmbeddingModel(),
        )
        self.model_patch.start()
        self.addCleanup(self.model_patch.stop)

    def test_ranks_relevant_tool_first(self):
        """Relevant tools should appear before less relevant tools."""
        results = retriever.retrieve_tools("query_duplicate", top_k=2)

        self.assertTrue(results)
        self.assertEqual(results[0]["name"], "duplicate_detector")

        scores = [item["similarity_score"] for item in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_returns_only_latest_approved_version(self):
        """Older and unapproved versions should not be returned."""
        results = retriever.retrieve_tools("query_duplicate", top_k=10)

        duplicate_results = [
            item for item in results
            if item["name"] == "duplicate_detector"
        ]

        self.assertEqual(len(duplicate_results), 1)
        self.assertEqual(duplicate_results[0]["version"], 2)

    def test_excludes_unapproved_tools(self):
        """Tools that failed validation must not be retrieved."""
        results = retriever.retrieve_tools("query_duplicate", top_k=10)

        names = [item["name"] for item in results]

        self.assertNotIn("failed_tool", names)

        # The unapproved version 3 must not replace approved version 2.
        duplicate_tool = next(
            item for item in results
            if item["name"] == "duplicate_detector"
        )
        self.assertEqual(duplicate_tool["version"], 2)

    def test_returns_similarity_scores(self):
        """Every result should include a valid similarity score."""
        results = retriever.retrieve_tools("query_duplicate")

        self.assertTrue(results)

        for result in results:
            self.assertIn("similarity_score", result)
            self.assertIsInstance(result["similarity_score"], float)
            self.assertGreaterEqual(result["similarity_score"], -1.0)
            self.assertLessEqual(result["similarity_score"], 1.0)

    def test_empty_query_returns_empty_list(self):
        """Empty or whitespace-only queries should return no results."""
        self.assertEqual(retriever.retrieve_tools(""), [])
        self.assertEqual(retriever.retrieve_tools("   "), [])

    def test_invalid_top_k_is_rejected(self):
        """top_k must be a positive integer."""
        invalid_values = [0, -1, 1.5, True, "3", None]

        for value in invalid_values:
            with self.subTest(top_k=value):
                with self.assertRaises(ValueError):
                    retriever.retrieve_tools(
                        "query_duplicate",
                        top_k=value,
                    )

    def test_min_score_filters_candidates(self):
        """A threshold of 1.0 should filter out imperfect matches."""
        results = retriever.retrieve_tools(
            "query_duplicate",
            top_k=10,
            min_score=1.0,
        )

        self.assertEqual(results, [])

    def test_invalid_min_score_is_rejected(self):
        """min_score must be a finite number between -1 and 1."""
        invalid_values = [
            -1.1,
            1.1,
            float("inf"),
            float("-inf"),
            float("nan"),
            True,
            "0.5",
        ]

        for value in invalid_values:
            with self.subTest(min_score=value):
                with self.assertRaises(ValueError):
                    retriever.retrieve_tools(
                        "query_duplicate",
                        min_score=value,
                    )

    def test_top_k_limits_result_count(self):
        """The number of returned tools must not exceed top_k."""
        results = retriever.retrieve_tools("query_duplicate", top_k=1)

        self.assertEqual(len(results), 1)

    def test_empty_registry_returns_empty_list(self):
        """Retrieval should handle a registry with no tools."""
        with patch.object(
            retriever.registry,
            "load_registry",
            return_value={"tools": {}},
        ):
            results = retriever.retrieve_tools("find duplicate records")

        self.assertEqual(results, [])

    def test_tool_document_includes_searchable_metadata(self):
        """Tool embeddings should include descriptions and capabilities."""
        tool = approved_tool(
            "csv_cleaner",
            "Clean missing values in CSV datasets",
            capabilities=["data cleaning", "CSV processing"],
            input_schema={"filename": "string"},
            output_schema={"cleaned_rows": "integer"},
        )

        document = retriever._tool_document(tool)

        self.assertIn("csv_cleaner", document)
        self.assertIn("Clean missing values", document)
        self.assertIn("data cleaning", document)
        self.assertIn("filename", document)
        self.assertIn("cleaned_rows", document)


if __name__ == "__main__":
    unittest.main()
