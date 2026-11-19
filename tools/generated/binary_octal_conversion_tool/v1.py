def run(input_data: dict) -> dict:
    """Convert binary string to octal string.

    Args:
        input_data (dict): Must contain a key "binary" with a string of 0s and 1s.

    Returns:
        dict: A dictionary with key "octal" containing the octal representation.
    """
    binary_str = input_data.get("binary", "")
    # Validate input: must be non‑empty and contain only 0 or 1
    if not binary_str or any(ch not in "01" for ch in binary_str):
        raise ValueError("Input must be a non‑empty binary string consisting of 0 and 1 characters.")
    # Convert binary to integer, then to octal string without the '0o' prefix
    integer_value = int(binary_str, 2)
    octal_str = oct(integer_value)[2:]
    return {"octal": octal_str}
