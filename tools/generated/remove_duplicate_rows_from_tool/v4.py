import csv
import io

def run(input_data: dict) -> dict:
    """Detect duplicate rows in the provided data.

    The function supports two input formats:
    1. {'ids': [...]} – a list of hash‑able values representing rows.
    2. {'csv_content': '...'} – a string containing CSV formatted text.

    It returns a dictionary with a single key ``duplicates`` whose value is a
    list of duplicate entries (as strings). The list is sorted to provide a
    deterministic order.
    """
    duplicates = set()
    seen = set()

    # Case 1: list of identifiers
    if "ids" in input_data:
        for item in input_data["ids"]:
            if item in seen:
                duplicates.add(item)
            else:
                seen.add(item)
        # Convert to sorted list for deterministic output
        return {"duplicates": sorted(duplicates)}

    # Case 2: raw CSV content
    if "csv_content" in input_data:
        csv_text = input_data["csv_content"]
        f = io.StringIO(csv_text)
        reader = csv.reader(f)
        rows = []
        for row in reader:
            # Represent each row as a tuple for hashability
            row_tuple = tuple(row)
            if row_tuple in seen:
                duplicates.add(",".join(row))
            else:
                seen.add(row_tuple)
                rows.append(row)
        return {"duplicates": sorted(duplicates)}

    # If neither key is present, return empty duplicate list
    return {"duplicates": []}
