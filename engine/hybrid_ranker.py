"""Hybrid ranking algorithm combining semantic similarity with metadata."""

from typing import List, Dict, Tuple, Any
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import config


def normalize_values(values: List[float]) -> np.ndarray:
    """Normalize a list of values to [0, 1] range.

    Args:
        values: List of numeric values to normalize.

    Returns:
        np.ndarray: Normalized values.
    """
    if not values:
        return np.array([])
    return MinMaxScaler().fit_transform(np.array(values).reshape(-1, 1)).flatten()


def calculate_genre_overlap(genres_a: List[str], genres_b: List[str]) -> float:
    """Calculate Jaccard similarity between two genre lists.

    Args:
        genres_a: First list of genres.
        genres_b: Second list of genres.

    Returns:
        float: Similarity score between 0 and 1.
    """
    if not genres_a or not genres_b:
        return 0.0

    set_a = set(genres_a)
    set_b = set(genres_b)

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    return intersection / union if union > 0 else 0.0


def rank_candidates(candidates: List[Dict], reference_genres: List[str]) -> List[Tuple[float, Dict]]:
    """Rank candidates using hybrid scoring algorithm.

    Combines semantic similarity, genre overlap, popularity, and rating scores.

    Args:
        candidates: List of candidate documents with scores.
        reference_genres: Genres from reference document for similarity.

    Returns:
        List[Tuple[float, Dict]]: Ranked list of (score, document) tuples.
    """
    if not candidates:
        return []

    # Extract scores
    semantic_scores = [c.get("semantic", 0.0) for c in candidates]
    popularity_scores = [c.get("popularity", 0) for c in candidates]
    rating_scores = [c.get("rating", 0) for c in candidates]

    # Normalize metadata scores
    normalized_popularity = normalize_values(popularity_scores)
    normalized_rating = normalize_values(rating_scores)

    # Calculate hybrid scores
    ranked = []
    for candidate, pop_norm, rating_norm in zip(candidates, normalized_popularity, normalized_rating):
        genre_overlap = calculate_genre_overlap(reference_genres, candidate.get("genres", []))

        # Weighted combination
        total_score = (
            config.SEMANTIC_WEIGHT * candidate["semantic"] +
            config.GENRE_OVERLAP_WEIGHT * genre_overlap +
            config.POPULARITY_WEIGHT * pop_norm +
            config.RATING_WEIGHT * rating_norm
        )

        ranked.append((total_score, candidate["doc"]))

    # Sort by score descending
    return sorted(ranked, key=lambda x: x[0], reverse=True)
