"""Build sentence embeddings for all documents in the database."""

import pickle
from sentence_transformers import SentenceTransformer
from db.mongo import get_documents
from engine.text_builder import build_text
import config


def main() -> None:
    """Build and save embeddings for all documents."""
    print("Loading documents from database...")
    docs = get_documents()

    if not docs:
        print("No documents found in database. Run data import first.")
        return

    print(f"Building text representations for {len(docs)} documents...")
    texts = [build_text(d) for d in docs]

    print("Loading sentence transformer model...")
    model = SentenceTransformer(config.SENTENCE_TRANSFORMER_MODEL)

    print("Generating embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True)

    print("Saving embeddings...")
    with open(config.EMBEDDINGS_FILE, "wb") as f:
        pickle.dump({"embeddings": embeddings}, f)

    print(f"Embeddings saved to {config.EMBEDDINGS_FILE}")
    print("Embeddings build complete!")


if __name__ == "__main__":
    main()
