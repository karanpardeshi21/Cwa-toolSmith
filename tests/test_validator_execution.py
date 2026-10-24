
import unittest

from validator import run_test_case, validate_tool


class TestRunTestCase(unittest.TestCase):

    def test_correct_output_passes(self):
        code = """
def run(input_data: dict) -> dict:
    return {"total": sum(input_data["numbers"])}
"""
        test_case = {
            "input": {"numbers": [1, 2, 3]},
            "expected": {"total": 6},
        }

        result = run_test_case(code, test_case)

        self.assertTrue(result["passed"])
        self.assertEqual(result["actual"], {"total": 6})

    def test_incorrect_output_fails(self):
        code = """
def run(input_data: dict) -> dict:
    return {"total": 100}
"""
        test_case = {
            "input": {"numbers": [1, 2, 3]},
            "expected": {"total": 6},
        }

        result = run_test_case(code, test_case)

        self.assertFalse(result["passed"])
        self.assertEqual(result["actual"], {"total": 100})

    def test_non_dictionary_output_fails(self):
        code = """
def run(input_data: dict) -> dict:
    return 42
"""
        result = run_test_case(
            code,
            {"input": {}, "expected": {}},
        )

        self.assertFalse(result["passed"])
        self.assertIn("dictionary", result["error"])

    def test_invalid_test_case_fails(self):
        result = run_test_case(
            "def run(input_data): return {}",
            {"input": [], "expected": {}},
        )

        self.assertFalse(result["passed"])
        self.assertIn("input dictionary", result["error"])

    def test_timeout_fails(self):
        code = """
def run(input_data: dict) -> dict:
    while True:
        pass
"""
        result = run_test_case(
            code,
            {"input": {}, "expected": {}},
            timeout=1,
        )

        self.assertFalse(result["passed"])
        self.assertIn("timed out", result["error"])


class TestValidateTool(unittest.TestCase):

    def test_valid_tool_passes(self):
        code = """
def run(input_data: dict) -> dict:
    return {"total": sum(input_data["numbers"])}
"""
        tests = [
            {
                "input": {"numbers": [1, 2, 3]},
                "expected": {"total": 6},
            }
        ]

        result = validate_tool(code, tests)

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["passed"])
        self.assertTrue(result["syntax_valid"])
        self.assertEqual(result["tests_passed"], 1)
        self.assertEqual(result["tests_failed"], 0)
        self.assertEqual(result["errors"], [])

    def test_failed_test_fails_validation(self):
        code = """
def run(input_data: dict) -> dict:
    return {"total": 100}
"""
        tests = [
            {
                "input": {"numbers": [1, 2, 3]},
                "expected": {"total": 6},
            }
        ]

        result = validate_tool(code, tests)

        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["passed"])
        self.assertEqual(result["tests_failed"], 1)
        self.assertTrue(result["errors"])

    def test_invalid_syntax_fails_validation(self):
        result = validate_tool("def run(:", [])

        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["syntax_valid"])

    def test_empty_tests_fail_validation(self):
        code = """
def run(input_data: dict) -> dict:
    return {}
"""
        result = validate_tool(code, [])

        self.assertFalse(result["passed"])
        self.assertIn("At least one test case", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
