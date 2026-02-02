"""Load anime and manga JSON data into MongoDB."""

import json
from pathlib import Path
from typing import List, Dict
from db.mongo import get_collection, insert_documents, create_indexes
import config


def load_json_file(filepath: Path) -> List[Dict]:
    """Load JSON file into memory.

    Args:
        filepath: Path to the JSON file.

    Returns:
        List[Dict]: List of documents from the JSON file.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in file {filepath}: {e}")


def main() -> None:
    """Load JSON data into MongoDB collection."""
    # For now, using a hardcoded file - in production, this should be configurable
    json_file = config.DATA_DIR / "anime_manga_all_anilist.json"

    print(f"Loading JSON file: {json_file}")
    try:
        items = load_json_file(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON: {e}")
        return

    if not items:
        print("No items found in JSON file.")
        return

    print(f"Loaded {len(items)} documents from JSON.")

    print("Inserting data into MongoDB...")
    try:
        insert_documents(items)
    except Exception as e:
        print(f"Error inserting documents: {e}")
        return

    print("Creating database indexes...")
    try:
        create_indexes()
    except Exception as e:
        print(f"Error creating indexes: {e}")
        return

    print("MongoDB import complete!")


if __name__ == "__main__":
    main()
