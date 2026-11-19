def run(input_data: dict) -> dict:
    """Convert a binary string to a decimal integer.

    Parameters
    ----------
    input_data: dict
        Expected to contain a key ``"binary"`` whose value is a string
        consisting only of the characters ``0`` and ``1``.

    Returns
    -------
    dict
        A dictionary with a single key ``"decimal"`` mapping to the integer
        value of the binary input.

    Raises
    ------
    ValueError
        If the ``binary`` key is missing, not a string, or contains characters
        other than ``0`` or ``1``.
    """
    # Retrieve the binary string
    binary = input_data.get("binary")
    if not isinstance(binary, str):
        raise ValueError("Input must contain a 'binary' key with a string value.")
    if not binary:
        raise ValueError("Binary string cannot be empty.")
    if any(ch not in "01" for ch in binary):
        raise ValueError("Binary string may contain only '0' and '1' characters.")

    # Perform conversion using built‑in int with base 2
    decimal_value = int(binary, 2)
    return {"decimal": decimal_value}
