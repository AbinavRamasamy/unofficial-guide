"""
Entry point for the Rutgers Unofficial Guide pipeline.
Runs ingestion → chunking → embedding → generation in order.
"""

from src.ingest import ingest
from src.embed import build_index
from src.generate import generate

if __name__ == "__main__":
    print("=== Step 1: Ingest + Chunk ===")
    ingest()

    print("\n=== Step 2: Embed + Index ===")
    build_index()

    print("\n=== Step 3: Generate ===")
    query = input("\nEnter a question: ").strip()
    if query:
        answer, sources = generate(query)
        print(answer)
        print(sources)
