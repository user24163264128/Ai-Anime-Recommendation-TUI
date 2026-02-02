"""Core recommendation engine using semantic search and hybrid ranking."""

from typing import List, Dict, Tuple, Optional
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from db.mongo import get_documents
from engine.text_builder import build_text
from engine.hybrid_ranker import rank_candidates
import config


class Recommender:
    """AI-powered recommendation engine for anime and manga."""

    def __init__(self):
        """Initialize the recommender with pre-built embeddings and index."""
        try:
            # Load embeddings
            with open(config.EMBEDDINGS_FILE, "rb") as f:
                self.embeddings_data = pickle.load(f)

            # Load FAISS index
            self.index = faiss.read_index(str(config.FAISS_INDEX_FILE))

            # Load sentence transformer model
            self.model = SentenceTransformer(config.SENTENCE_TRANSFORMER_MODEL)

            # Load documents
            self.documents = get_documents()

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Required data file not found: {e}. Run build scripts first.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize recommender: {e}")

    def _search_similar(self, query_vector: np.ndarray, k: int = config.DEFAULT_SEARCH_K) -> List[Dict]:
        """Search for semantically similar documents using FAISS.

        Args:
            query_vector: Normalized query embedding vector.
            k: Number of candidates to retrieve.

        Returns:
            List[Dict]: Candidate documents with similarity scores.
        """
        # Ensure vector is normalized
        faiss.normalize_L2(query_vector)

        # Search index
        scores, indices = self.index.search(query_vector, min(k, len(self.documents)))

        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < len(self.documents):
                doc = self.documents[idx]
                results.append({
                    "doc": doc,
                    "semantic": float(score),
                    "genres": doc.get("genres", []),
                    "popularity": doc.get("popularity", 0),
                    "rating": doc.get("average_score", 0),
                })

        return results

    def by_text(self, query: str, n: int = config.DEFAULT_RESULTS_N) -> List[Tuple[float, Dict]]:
        """Recommend items based on text description.

        Args:
            query: Natural language description of desired content.
            n: Number of recommendations to return.

        Returns:
            List[Tuple[float, Dict]]: Ranked list of (score, document) tuples.
        """
        if not query.strip():
            return []

        # Generate query embedding
        query_vector = self.model.encode([query], convert_to_numpy=True).astype("float32")

        # Find candidates
        candidates = self._search_similar(query_vector)

        # Rank with hybrid algorithm (no reference genres for text search)
        return rank_candidates(candidates, [])[:n]

    def by_title(self, title: str, n: int = config.DEFAULT_RESULTS_N) -> List[Tuple[float, Dict]]:
        """Recommend items similar to a given title.

        Args:
            title: Title to find similar content for.
            n: Number of recommendations to return.

        Returns:
            List[Tuple[float, Dict]]: Ranked list of (score, document) tuples.

        Raises:
            ValueError: If title is not found in database.
        """
        if not title.strip():
            return []

        # Find reference document
        reference_doc = None
        for doc in self.documents:
            if title.lower() in (doc.get("title_romaji") or "").lower() or \
               title.lower() in (doc.get("title_english") or "").lower():
                reference_doc = doc
                break

        if not reference_doc:
            raise ValueError(f"Title '{title}' not found in database")

        # Generate embedding for reference document
        ref_text = build_text(reference_doc)
        ref_vector = self.model.encode([ref_text], convert_to_numpy=True).astype("float32")

        # Find candidates
        candidates = self._search_similar(ref_vector)

        # Rank with hybrid algorithm using reference genres
        ref_genres = reference_doc.get("genres", [])
        return rank_candidates(candidates, ref_genres)[:n]
