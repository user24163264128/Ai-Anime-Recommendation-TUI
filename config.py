"""Configuration constants for the recommendation system."""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DB_DIR = PROJECT_ROOT / "db"
ENGINE_DIR = PROJECT_ROOT / "engine"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Data files
EMBEDDINGS_FILE = DATA_DIR / "embeddings.pkl"
FAISS_INDEX_FILE = DATA_DIR / "faiss.index"

# Database configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "anime_manga_db"
COLLECTION_NAME = "titles"

# Model configuration
SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Ranking weights
SEMANTIC_WEIGHT = 0.65
GENRE_OVERLAP_WEIGHT = 0.20
POPULARITY_WEIGHT = 0.10
RATING_WEIGHT = 0.05

# Search defaults
DEFAULT_SEARCH_K = 50
DEFAULT_RESULTS_N = 10