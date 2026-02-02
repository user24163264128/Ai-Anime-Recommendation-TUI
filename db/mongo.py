"""MongoDB database operations for the recommendation system."""

from typing import List, Dict, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, OperationFailure
import config


def get_collection() -> Collection:
    """Connect to MongoDB and return the titles collection.

    Returns:
        Collection: MongoDB collection for titles.

    Raises:
        ConnectionFailure: If unable to connect to MongoDB.
    """
    try:
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')
        return client[config.DB_NAME][config.COLLECTION_NAME]
    except ConnectionFailure as e:
        raise ConnectionFailure(f"Failed to connect to MongoDB at {config.MONGO_URI}: {e}")


def get_documents() -> List[Dict]:
    """Retrieve all documents from the titles collection.

    Returns:
        List[Dict]: List of all title documents.

    Raises:
        OperationFailure: If database operation fails.
    """
    try:
        collection = get_collection()
        return list(collection.find())
    except OperationFailure as e:
        raise OperationFailure(f"Failed to retrieve documents: {e}")


def get_all_titles() -> List[str]:
    """Retrieve all title names for autocomplete.

    Returns:
        List[str]: List of title strings (romaji or english).

    Raises:
        OperationFailure: If database operation fails.
    """
    try:
        collection = get_collection()
        titles = []
        for doc in collection.find({}, {"title_romaji": 1, "title_english": 1}):
            title = doc.get("title_romaji") or doc.get("title_english")
            if title:
                titles.append(title)
        return titles
    except OperationFailure as e:
        raise OperationFailure(f"Failed to retrieve titles: {e}")


def insert_documents(documents: List[Dict]) -> None:
    """Insert multiple documents into the collection.

    Args:
        documents: List of documents to insert.

    Raises:
        OperationFailure: If insertion fails.
    """
    if not documents:
        return

    try:
        collection = get_collection()
        collection.insert_many(documents)
    except OperationFailure as e:
        raise OperationFailure(f"Failed to insert documents: {e}")


def create_indexes() -> None:
    """Create database indexes for efficient queries.

    Raises:
        OperationFailure: If index creation fails.
    """
    try:
        collection = get_collection()
        collection.create_index("id", unique=True)
        collection.create_index("type")
        collection.create_index("title_romaji")
        collection.create_index("genres")
        collection.create_index("tags")
        collection.create_index("source")
    except OperationFailure as e:
        raise OperationFailure(f"Failed to create indexes: {e}")
