"""
Milestone 4 — Embedding and Retrieval
Pipeline: Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation

This script does two things:
  1. build_index() — loads chunks.json, embeds every chunk with all-MiniLM-L6-v2,
                     and stores the vectors + metadata in ChromaDB.
  2. retrieve(query, k) — embeds a query and returns the top-k most similar chunks.

Run once to build the index, then import retrieve() in your generation script.
"""

import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

# ── Config ────────────────────────────────────────────────────────────────────

ROOT          = Path(__file__).parent.parent  # project root (one level above src/)
CHUNKS_PATH   = ROOT / "documents/chunks.json"
CHROMA_DIR    = ROOT / "documents/chroma_db"  # ChromaDB persists to disk here
COLLECTION    = "rutgers_reviews"             # name for our vector collection
EMBED_MODEL   = "all-MiniLM-L6-v2"
TOP_K         = 5                             # chunks returned per query (planning.md)
BATCH_SIZE    = 64                            # how many chunks to embed at once


# ── Embedding + indexing ──────────────────────────────────────────────────────

def build_index():
    """
    Embed every chunk and store it in ChromaDB.
    Safe to re-run — clears the old collection and rebuilds from scratch.
    """
    # Load chunks produced by ingest.py
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"[embed]  Loaded {len(chunks)} chunks from {CHUNKS_PATH}")

    # Load the embedding model (downloads ~90 MB on first run, cached after)
    model = SentenceTransformer(EMBED_MODEL)
    print(f"[embed]  Model loaded: {EMBED_MODEL}")

    # -- ChromaDB setup --------------------------------------------------------
    #
    # PersistentClient stores the database on disk at CHROMA_DIR.
    # Every time you run this script the data survives — you don't need to
    # re-embed unless your chunks change.
    #
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # A "collection" is like a table — it holds vectors, text, and metadata.
    # get_or_create_collection returns the existing one or makes a new one.
    # We delete first so re-runs start clean instead of appending duplicates.
    # Delete only if it already exists to avoid an error on first run
    existing = [c.name for c in client.list_collections()]
    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
    collection = client.get_or_create_collection(
        name=COLLECTION,
        # ChromaDB supports several distance metrics; cosine is standard for
        # sentence embeddings because it measures direction, not magnitude.
        metadata={"hnsw:space": "cosine"},
    )
    print(f"[embed]  Collection '{COLLECTION}' ready")

    # -- Embed in batches and upsert -------------------------------------------
    #
    # collection.add() takes four parallel lists:
    #   ids        — a unique string ID for each chunk (required by ChromaDB)
    #   embeddings — the float vectors from our model
    #   documents  — the raw text (stored so we can return it at query time)
    #   metadatas  — any extra fields we want to filter or display (source, url)
    #
    total = len(chunks)
    for start in range(0, total, BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]

        texts      = [c["text"]              for c in batch]
        ids        = [f"chunk_{start + i}"   for i in range(len(batch))]
        metadatas  = [{"source": c.get("source", ""), "url": c.get("url", "")}
                      for c in batch]

        # encode() returns a numpy array of shape (batch_size, 384)
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        print(f"[embed]  {min(start + BATCH_SIZE, total)}/{total} chunks indexed")

    print(f"\n[embed]  Done. {total} chunks stored in {CHROMA_DIR}")
    return collection


# ── Retrieval ─────────────────────────────────────────────────────────────────

def get_collection():
    """Open the persisted ChromaDB collection (no re-embedding needed)."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(COLLECTION)


def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """
    Embed the query and return the top-k most similar chunks.

    -- How ChromaDB query() works -----------------------------------------------
    collection.query() takes:
      query_embeddings — the embedded query vector (as a nested list)
      n_results        — how many nearest neighbours to return
      include          — which fields to include in the response

    It returns a dict of parallel lists:
      result["documents"][0]  — list of the k chunk texts
      result["metadatas"][0]  — list of metadata dicts (source, url)
      result["distances"][0]  — list of cosine distances (lower = more similar)

    The [0] indexing is because ChromaDB supports batched queries (multiple
    queries at once); we only send one, so we take the first result set.
    -----------------------------------------------------------------------------
    """
    model = SentenceTransformer(EMBED_MODEL)
    query_embedding = model.encode(query).tolist()

    collection = get_collection()
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Zip the parallel lists into a clean list of dicts
    chunks = []
    for text, meta, dist in zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        chunks.append({
            "text":     text,
            "source":   meta.get("source", ""),
            "url":      meta.get("url", ""),
            "distance": round(dist, 4),   # cosine distance: 0 = identical, 2 = opposite
        })
    return chunks


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Build the index (only needs to run once, or when chunks.json changes)
    build_index()

    # Test retrieval with two sample queries from the evaluation plan
    test_queries = [
        "which professor should I take for CS111",
        "easiest professor for MATH151",
    ]

    model_loaded = SentenceTransformer(EMBED_MODEL)  # reuse same model instance
    collection   = get_collection()

    for query in test_queries:
        print(f"\n{'─'*60}")
        print(f"Query: {query}")
        print('─'*60)
        results = retrieve(query)
        for i, chunk in enumerate(results, 1):
            print(f"\n[{i}] distance={chunk['distance']}  source={chunk['source']}")
            print(chunk["text"][:300] + ("..." if len(chunk["text"]) > 300 else ""))
