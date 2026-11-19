def run(input_data: dict) -> dict:
    """Return duplicate entries from the provided list.

    Args:
        input_data (dict): Must contain the key "ids" with a list of hashable items.

    Returns:
        dict: A dictionary with a single key "duplicates" whose value is a list of items that occur more than once in the input, ordered by the first time each duplicate is encountered.
    """
    ids = input_data.get("ids", [])
    seen = set()
    duplicates = []
    added = set()
    for item in ids:
        if item in seen:
            if item not in added:
                duplicates.append(item)
                added.add(item)
        else:
            seen.add(item)
    return {"duplicates": duplicates}
