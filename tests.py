"""Basic tests for the recommendation system components."""

import pytest
from engine.text_builder import build_text
from engine.hybrid_ranker import calculate_genre_overlap, normalize_values
from db.mongo import get_collection


def test_build_text():
    """Test text building from document."""
    doc = {
        "title_romaji": "Test Anime",
        "title_english": "Test Anime EN",
        "genres": ["Action", "Adventure"],
        "tags": ["Shounen", "Fighting"],
        "description": "A great anime about heroes."
    }

    text = build_text(doc)
    assert "Test Anime" in text
    assert "Test Anime EN" in text
    assert "Action" in text
    assert "Adventure" in text
    assert "Shounen" in text
    assert "Fighting" in text
    assert "heroes" in text


def test_genre_overlap():
    """Test genre overlap calculation."""
    genres_a = ["Action", "Adventure", "Comedy"]
    genres_b = ["Action", "Adventure", "Drama"]

    overlap = calculate_genre_overlap(genres_a, genres_b)
    assert overlap == 2/4  # 2 common out of 4 total unique

    # Empty genres
    assert calculate_genre_overlap([], ["Action"]) == 0.0
    assert calculate_genre_overlap(["Action"], []) == 0.0


def test_normalize_values():
    """Test value normalization."""
    values = [1, 2, 3, 4, 5]
    normalized = normalize_values(values)

    assert len(normalized) == 5
    assert normalized[0] == 0.0  # min value
    assert normalized[-1] == 1.0  # max value

    # Empty list
    assert len(normalize_values([])) == 0


def test_mongo_connection():
    """Test MongoDB connection (requires running MongoDB)."""
    try:
        collection = get_collection()
        # Just test that we can get a collection object
        assert collection is not None
        assert collection.name == "titles"
    except Exception:
        pytest.skip("MongoDB not available for testing")


if __name__ == "__main__":
    pytest.main([__file__])