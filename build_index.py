"""
Builds a persistent Chroma vector store from data/catalog.json using a local
sentence-transformers embedding model (no API key needed, runs on CPU).

Run once (or whenever the catalog changes):
    python build_index.py
"""

import json
import chromadb
from sentence_transformers import SentenceTransformer

CATALOG_PATH = "data/catalog.json"
CHROMA_DIR = "data/chroma_db"
COLLECTION_NAME = "shl_catalog"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, good enough for this catalog size


def main():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print(f"Loaded {len(catalog)} assessments.")
    print("Loading embedding model (first run downloads ~90MB)...")
    model = SentenceTransformer(EMBED_MODEL_NAME)

    texts = [item["search_text"] for item in catalog]
    print("Encoding embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    # start fresh each build
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(
        COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    ids = [item["id"] for item in catalog]
    metadatas = [
        {
            "name": item["name"],
            "url": item["url"],
            "test_type": ",".join(item["test_type"]),
            "duration": item["duration"],
            "remote_testing": item["remote_testing"],
            "adaptive_irt": item["adaptive_irt"],
            "job_levels": ",".join(item["job_levels"]),
        }
        for item in catalog
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas,
    )

    print(f"Indexed {collection.count()} assessments into Chroma at {CHROMA_DIR}")


if __name__ == "__main__":
    main()
