"""Isolate untrusted text so retrieved data cannot become instructions."""

_CLOSE = "</untrusted_data>"


def wrap_untrusted(source: str, text: str) -> str:
    """Wrap external content. Nested close tags are stripped, not interpreted."""
    cleaned = text.replace(_CLOSE, "")
    label = source.replace('"', "'")
    return f'<untrusted_data source="{label}">\n{cleaned}\n{_CLOSE}'
