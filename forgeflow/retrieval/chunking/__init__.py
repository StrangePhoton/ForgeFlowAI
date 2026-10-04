"""Heading-aware packing of manual text into overlapping chunks."""


def chunk_text(text: str, *, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return []
    paragraphs = [block.strip() for block in cleaned.split("\n\n") if block.strip()]
    packed: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        candidate = paragraph if not buffer else f"{buffer}\n\n{paragraph}"
        if len(candidate) <= chunk_size:
            buffer = candidate
            continue
        if buffer:
            packed.append(buffer)
        if len(paragraph) <= chunk_size:
            buffer = paragraph
        else:
            packed.extend(_window(paragraph, chunk_size, overlap))
            buffer = ""
    if buffer:
        packed.append(buffer)
    return packed or [cleaned[:chunk_size]]


def _window(text: str, chunk_size: int, overlap: int) -> list[str]:
    step = max(1, chunk_size - overlap)
    return [text[index : index + chunk_size] for index in range(0, len(text), step)]
