"""
ExperimentIQ — Day 6, Task 2: Embed + Load ChromaDB
=====================================================
Takes the chunks produced by Task 1, generates embeddings using
sentence-transformers, and loads them into a persistent ChromaDB collection.

WHY THIS DESIGN:
- all-MiniLM-L6-v2 is the community default for RAG use cases: fast,
  lightweight (80MB), and strong for semantic similarity on English text.
  Bigger models (e.g. all-mpnet-base-v2) give marginally better results
  but are 5x slower — not worth it for a 15-doc knowledge base.
- We use ChromaDB's EphemeralClient for development (in-memory, zero setup)
  and PersistentClient for production (saves to disk, survives restarts).
  The flag `persist=True` switches between them.
- We pass metadata (source_doc, chunk_index, word_count) into ChromaDB.
  This lets your retriever later filter by document — e.g., "only retrieve
  from statistical methodology docs, not decision framework docs."
- Batch size of 32 is a safe default — avoids memory spikes on large corpora
  while still being much faster than embedding one chunk at a time.

USAGE:
    # Standard run (in-memory, good for dev)
    python day6_task2_embed_load.py

    # Persist to disk (for production use in the app)
    python day6_task2_embed_load.py --persist

    # Run tests only
    python day6_task2_embed_load.py --test

    # Test retrieval after loading
    python day6_task2_embed_load.py --query "what is statistical power"

PREREQUISITES:
    pip install sentence-transformers chromadb
    Run Task 1 first (or import chunk_corpus from day6_task1_chunker.py)

HOW TO TEST (see bottom of file or run --test flag):
    1. Smoke test: collection created, right number of items loaded
    2. Retrieval test: semantic query returns relevant chunk, not random one
    3. Metadata test: returned chunks have all expected fields
    4. Deduplication test: re-running doesn't double-load
"""

import os
import argparse
from typing import List

# ─────────────────────────────────────────────────────────────
# Imports with friendly error messages
# ─────────────────────────────────────────────────────────────

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "\n sentence-transformers not installed.\n"
        "   Run: pip install sentence-transformers\n"
        "   Note: this downloads ~80MB model on first run.\n"
    )

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    raise ImportError(
        "\n chromadb not installed.\n"
        "   Run: pip install chromadb\n"
    )

# Import from Task 1
from chunker import Chunk, chunk_corpus, CORPUS_FOLDER


# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # 80MB, fast, strong for RAG
COLLECTION_NAME = "experimentiq_kb"     # the ChromaDB collection name
CHROMA_DB_PATH  = "./chroma_db"         # local folder for persistent storage
EMBED_BATCH_SIZE = 32                   # chunks per embedding batch


# ─────────────────────────────────────────────────────────────
# Embedding
# ─────────────────────────────────────────────────────────────

def load_embedding_model(model_name: str = EMBEDDING_MODEL) -> SentenceTransformer:
    """
    Loads the sentence-transformer model.
    First call downloads ~80MB from HuggingFace Hub (cached after that).

    WHAT TO EXPECT ON FIRST RUN:
        Downloading: 100%|████████| 80.2M/80.2M [00:12<00:00, 6.43MiB/s]
        Load time: ~3-5 seconds

    WHAT TO EXPECT ON SUBSEQUENT RUNS:
        Load time: ~1 second (from local cache)
    """
    print(f"Loading embedding model: {model_name}")
    print("   (Downloads ~80MB on first run — cached after that)")
    model = SentenceTransformer(model_name)
    print(f"   ✓ Model loaded. Embedding dimension: {model.get_embedding_dimension()}")
    return model


def embed_chunks(chunks: List[Chunk], model: SentenceTransformer,
                 batch_size: int = EMBED_BATCH_SIZE) -> List[List[float]]:
    """
    Generates an embedding vector for each chunk's text.

    WHAT THE EMBEDDINGS ARE:
        Each chunk text → a 384-dimensional float vector.
        Semantically similar text → vectors close together in embedding space.
        This is what ChromaDB uses to find relevant chunks for a query.

    Args:
        chunks:     list of Chunk objects from Task 1
        model:      loaded SentenceTransformer model
        batch_size: how many chunks to embed at once (memory vs speed tradeoff)

    Returns:
        List of embedding vectors, parallel to `chunks`
    """
    texts = [c.text for c in chunks]
    total = len(texts)
    print(f"\n⚡ Embedding {total} chunks in batches of {batch_size}...")

    embeddings = []
    for i in range(0, total, batch_size):
        batch = texts[i : i + batch_size]
        batch_embeddings = model.encode(batch, show_progress_bar=False).tolist()
        embeddings.extend(batch_embeddings)

        # Progress indicator
        done = min(i + batch_size, total)
        pct = done / total * 100
        bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
        print(f"   [{bar}] {done:>4}/{total} ({pct:.0f}%)", end="\r")

    print(f"   ✓ All {total} chunks embedded.                          ")
    return embeddings
