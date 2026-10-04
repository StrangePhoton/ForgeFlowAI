"""Equipment-code extraction used when structured LLM output is incomplete."""

import re

_EQUIPMENT_CODE = re.compile(r"\b([A-Z]{2,}(?:-[A-Z0-9]+)+)\b", re.IGNORECASE)


def extract_equipment_code(text: str) -> str | None:
    match = _EQUIPMENT_CODE.search(text)
    if match is None:
        return None
    return match.group(1).upper()
