"""
Milestone 3 — Document Ingestion and Chunking
Pipeline: Document Ingestion → Chunking → (Embedding → Vector Store → Retrieval → Generation)

Sources:
  - documents/   : any .txt files you manually saved (e.g. copy-pasted RateMyProfessors reviews)
  - r/rutgers    : scraped via Reddit's RSS feed (no API key needed)

Chunking strategy: 250 tokens, 0 overlap.
Each post is treated as one standalone document — one post = one chunk.
Long posts get split at sentence boundaries to stay under the limit.

Run this script to produce two files:
  raw_documents.json  — raw text before any cleaning (for inspection)
  chunks.json         — cleaned, chunked text ready for Milestone 4 embedding
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent  # project root (one level above src/)
DOCUMENTS_DIR = ROOT / "documents"
CHUNK_SIZE = 250   # max tokens per chunk (matches planning.md)
OVERLAP = 0        # no overlap — reviews are self-contained

REDDIT_QUERIES = [
    "professor review",
    "which professor should I take",
    "course hard easy grade",
    "final exam midterm",
    "course evaluation",
]


# ── Ingestion ─────────────────────────────────────────────────────────────────

def load_local_documents():
    """Load every .txt file from documents/ for manually saved reviews."""
    docs = []
    for filepath in DOCUMENTS_DIR.glob("*.txt"):
        text = filepath.read_text(encoding="utf-8").strip()
        if text:
            docs.append({"source": filepath.name, "url": "", "raw": text})
    print(f"[local]   {len(docs)} files loaded from {DOCUMENTS_DIR}/")
    return docs


def scrape_reddit(query, subreddit="rutgers", limit=25):
    """
    Fetch posts via Reddit's RSS feed — no API key or login needed.
    The RSS <content> field is an HTML table; we extract only the
    actual selftext (post body) and strip all Reddit chrome.
    """
    rss_url = f"https://www.reddit.com/r/{subreddit}/search.rss"
    params = {"q": query, "sort": "top", "restrict_sr": "on"}
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

    try:
        resp = requests.get(rss_url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[reddit]  WARNING: RSS fetch failed for '{query}': {e}")
        return []

    soup = BeautifulSoup(resp.text, "xml")
    entries = soup.find_all("entry")[:limit]

    docs = []
    for entry in entries:
        title_tag = entry.find("title")
        content_tag = entry.find("content")
        link_tag = entry.find("link")

        title = title_tag.get_text(strip=True) if title_tag else ""
        post_url = link_tag.get("href", "") if link_tag else ""

        # The content field is raw HTML — parse it to pull out only real text
        body = ""
        if content_tag:
            inner = BeautifulSoup(content_tag.get_text(), "html.parser")
            # Remove image tags entirely (alt text duplicates the title)
            for img in inner.find_all("img"):
                img.decompose()
            # Remove the Reddit metadata links: [link], [comments]
            for a in inner.find_all("a"):
                if a.get_text(strip=True) in ("[link]", "[comments]"):
                    a.decompose()
            # Remove "submitted by /u/..." lines
            body = inner.get_text(separator=" ", strip=True)
            body = re.sub(r"submitted by\s+/?u/\S+", "", body)

        raw = f"{title}\n{body}".strip()
        if raw:
            docs.append({"source": f"r/{subreddit}", "url": post_url, "raw": raw})

    return docs


# ── Cleaning ──────────────────────────────────────────────────────────────────

def clean_text(raw):
    """
    Remove everything that isn't substantive review content.
    Keeps: review opinions, professor names, course numbers, ratings language.
    Removes: URLs, HTML entities, Reddit boilerplate, leftover punctuation clutter.
    """
    text = raw

    # HTML entities (&amp; &nbsp; &#32; etc.) → plain characters
    text = BeautifulSoup(text, "html.parser").get_text(separator=" ")

    # Remove bare URLs
    text = re.sub(r"https?://\S+", "", text)

    # Reddit markdown links [label](url) → just label
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Any remaining Reddit boilerplate lines
    text = re.sub(r"submitted by\s+/?u/\S+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[link\]|\[comments?\]", "", text, flags=re.IGNORECASE)

    # Non-content punctuation clutter (keep apostrophes, hyphens, basic punctuation)
    text = re.sub(r"[^\w\s.,!?'\"\-]", " ", text)

    # Collapse all whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ── Chunking ──────────────────────────────────────────────────────────────────

def count_tokens(text):
    """Approximate token count: ~1.3 tokens per English word."""
    return int(len(text.split()) * 1.3)


def chunk_text(text, source="", url="", chunk_size=CHUNK_SIZE):
    """
    Split a document into chunks of at most chunk_size tokens with no overlap.
    Short posts (most reviews) fit in one chunk.
    Long posts are split at sentence boundaries so no thought gets cut in half.
    """
    meta = {"source": source, "url": url}

    if count_tokens(text) <= chunk_size:
        return [{**meta, "text": text}]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current, current_tokens = [], [], 0

    for sentence in sentences:
        stokens = count_tokens(sentence)
        if current_tokens + stokens > chunk_size and current:
            chunks.append({**meta, "text": " ".join(current)})
            current, current_tokens = [], 0
        current.append(sentence)
        current_tokens += stokens

    if current:
        chunks.append({**meta, "text": " ".join(current)})

    return chunks


# ── Main pipeline ─────────────────────────────────────────────────────────────

def ingest():
    # ── Step 1: collect raw documents ──────────────────────────────────────────
    all_docs = []
    all_docs.extend(load_local_documents())
    for query in REDDIT_QUERIES:
        posts = scrape_reddit(query)
        print(f"[reddit]  {len(posts):>3} posts  ← '{query}'")
        all_docs.extend(posts)

    print(f"\n[ingest]  {len(all_docs)} total documents collected")

    # Save raw text before any cleaning so you can inspect what came in
    raw_path = DOCUMENTS_DIR / "raw_documents.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(all_docs, f, indent=2, ensure_ascii=False)
    print(f"[ingest]  Raw documents saved → {raw_path}")

    # ── Step 2: inspect one raw document ──────────────────────────────────────
    print("\n── Raw document sample (before cleaning) ─────────────────────────")
    print(all_docs[0]["raw"][:600] if all_docs else "(no documents)")
    print("──────────────────────────────────────────────────────────────────\n")

    # ── Step 3: clean every document ──────────────────────────────────────────
    cleaned_docs = []
    skipped = 0
    for doc in all_docs:
        cleaned = clean_text(doc["raw"])
        # Drop documents that are too short to be useful after cleaning
        if len(cleaned.split()) < 5:
            skipped += 1
            continue
        cleaned_docs.append({**doc, "cleaned": cleaned})

    print(f"[clean]   {skipped} documents dropped (too short after cleaning)")

    # Inspect one cleaned document — read this and make sure it looks right
    print("── Cleaned document sample (after cleaning) ──────────────────────")
    print(cleaned_docs[0]["cleaned"][:600] if cleaned_docs else "(no documents)")
    print("──────────────────────────────────────────────────────────────────\n")

    # ── Step 4: chunk every cleaned document ──────────────────────────────────
    chunks = []
    for doc in cleaned_docs:
        chunks.extend(chunk_text(doc["cleaned"], source=doc["source"], url=doc.get("url", "")))

    print(f"[chunk]   {len(chunks)} total chunks produced")

    # Print 5 representative chunks for inspection
    print("\n── 5 representative chunks ───────────────────────────────────────")
    step = max(1, len(chunks) // 5)
    for i, idx in enumerate(range(0, min(len(chunks), step * 5), step)):
        c = chunks[idx]
        print(f"\n[{i+1}] source={c['source']}  tokens=~{count_tokens(c['text'])}")
        print(c["text"][:300] + ("..." if len(c["text"]) > 300 else ""))
    print("──────────────────────────────────────────────────────────────────")

    return chunks


if __name__ == "__main__":
    chunks = ingest()

    out = DOCUMENTS_DIR / "chunks.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"\n[ingest]  Saved {len(chunks)} chunks → {out}")
