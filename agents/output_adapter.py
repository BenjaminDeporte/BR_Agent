import json
from typing import Any

def normalize_agent_output(output: Any) -> str:
    """
    Ensures the agent output is safe for UI display.
    Manages different data types: strings, lists, dicts, etc.
    1. If output is None, returns a default message.
    2. If output is a string, returns it as is.
    3. If output is a list, dict, or other structured data, converts it to a formatted JSON string.
    4. If JSON conversion fails, falls back to string representation.
    5. Returns the normalized string output.
    """
    if output is None:
        return "No output produced."

    if isinstance(output, str):
        return output

    # list / dict / other structured data
    try:
        return json.dumps(output, indent=2, ensure_ascii=False)
    except Exception:
        return str(output)
