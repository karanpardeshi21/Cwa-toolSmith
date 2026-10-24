def run(input_data: dict) -> dict:
    """Add two numbers.

    Parameters
    ----------
    input_data: dict
        Must contain numeric keys "a" and "b".

    Returns
    -------
    dict
        A dictionary with a single key "sum" representing the addition result.
    """
    a = input_data.get("a")
    b = input_data.get("b")
    # Ensure both values are present and are numbers
    if a is None or b is None:
        raise ValueError("Both 'a' and 'b' must be provided in the input.")
    return {"sum": a + b}
