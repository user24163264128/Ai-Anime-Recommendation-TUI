"""Build FAISS vector index for fast similarity search."""

import pickle
import faiss
import numpy as np
import config


def main() -> None:
    """Build and save FAISS index from embeddings."""
    print("Loading embeddings...")
    try:
        with open(config.EMBEDDINGS_FILE, "rb") as f:
            data = pickle.load(f)
    except FileNotFoundError:
        print(f"Embeddings file not found: {config.EMBEDDINGS_FILE}")
        print("Run build_embeddings.py first.")
        return

    vectors = np.array(data["embeddings"]).astype("float32")

    if vectors.size == 0:
        print("No embeddings found in file.")
        return

    print(f"Normalizing {len(vectors)} vectors...")
    faiss.normalize_L2(vectors)

    print("Building FAISS index...")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    print("Saving index...")
    faiss.write_index(index, str(config.FAISS_INDEX_FILE))

    print(f"FAISS index saved to {config.FAISS_INDEX_FILE}")
    print("Index build complete!")


if __name__ == "__main__":
    main()
