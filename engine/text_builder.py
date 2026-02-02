"""Text building utilities for creating searchable text from documents."""

from typing import Dict


def build_text(doc: Dict) -> str:
    """Build a searchable text string from a document.

    Combines title, genres, tags, and description into a single text string
    for embedding generation.

    Args:
        doc: Document dictionary containing title, genres, tags, and description.

    Returns:
        str: Combined text string for search indexing.
    """
    parts = [
        doc.get("title_romaji", ""),
        doc.get("title_english", ""),
        " ".join(doc.get("genres", [])),
        " ".join(doc.get("tags", [])),
        doc.get("description", ""),
    ]
    return " ".join(filter(None, parts))  # Filter out empty strings

