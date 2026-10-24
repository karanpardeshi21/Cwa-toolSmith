
import unittest

from validator import check_syntax, check_entry_point


class TestSyntaxValidation(unittest.TestCase):

    def test_valid_python_code(self):
        code = """
def run(input_data: dict) -> dict:
    return {"result": "success"}
"""
        result = check_syntax(code)

        self.assertTrue(result["valid"])
        self.assertIsNone(result["error"])

    def test_invalid_python_code(self):
        code = "def run(input_data: dict)\n    return {}"

        result = check_syntax(code)

        self.assertFalse(result["valid"])
        self.assertIsNotNone(result["error"])


class TestEntryPointValidation(unittest.TestCase):

    def test_run_function_exists(self):
        code = """
def run(input_data: dict) -> dict:
    return {}
"""
        result = check_entry_point(code)

        self.assertTrue(result["valid"])
        self.assertIsNone(result["error"])

    def test_run_function_missing(self):
        code = """
def calculate() -> int:
    return 10
"""
        result = check_entry_point(code)

        self.assertFalse(result["valid"])
        self.assertIn("run", result["error"])

    def test_async_run_is_rejected(self):
        code = """
async def run(input_data: dict) -> dict:
    return {}
"""
        result = check_entry_point(code)

        self.assertFalse(result["valid"])
        self.assertIn("async", result["error"])

    def test_syntax_error_is_reported_by_entry_check(self):
        code = "def run(:"

        result = check_entry_point(code)

        self.assertFalse(result["valid"])
        self.assertIn("syntax", result["error"].lower())


if __name__ == "__main__":
    unittest.main()
