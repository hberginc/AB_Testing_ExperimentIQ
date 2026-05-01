"""
Embed + Load ChromaDB:
Takes the chunks produced by chunker.py, generates encoding/embedding using
sentence-transformers, and loads them into a persistent ChromaDB collection.

WHY THIS DESIGN:
- all-MiniLM-L6-v2 is the community default for RAG use cases: fast,
  lightweight (80MB), and strong for semantic similarity on English text.
- We use ChromaDB's EphemeralClient for development (in-memory, zero setup)
  and PersistentClient for production (saves to disk, survives restarts).
  The flag `persist=True` switches between them.
- We pass metadata (source_doc, chunk_index, word_count) into ChromaDB.
  This lets retriever later filter by document (ex. "only retrieve
  from statistical methodology docs, not decision framework docs.")
- Batch size of 32 is a safe default, it avoids memory spikes on large document
  while still being much faster than embedding one chunk at a time.

USAGE:
    # Standard run (in-memory)
    python  embed_load.py

    # Persist to disk (for production use in the app)
    python  embed_load.py --persist

    # Run tests only
    python  embed_load.py --test

    # Test retrieval after loading
    python  embed_load.py --query "what is statistical power"

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


# ─────────────────────────────────────────────────────────────
# ChromaDB loading
# ─────────────────────────────────────────────────────────────

def get_chroma_client(persist: bool = False, db_path: str = CHROMA_DB_PATH):
    """
    Returns either an in-memory or persistent ChromaDB client.

    In-Memory (persist=False):
        - Lives in RAM only
        - Wiped when your Python process ends
        - Use during development to avoid stale data issues
        - Fast startup, no disk I/O

    PERSISTENT (persist=True):
        - Saved to ./chroma_db/ folder
        - Survives restarts — you only embed once
        - Check: ls -la ./chroma_db/ to see the SQLite files
    """
    if persist:
        os.makedirs(db_path, exist_ok=True)
        client = chromadb.PersistentClient(path=db_path)
        print(f"ChromaDB: persistent storage at {db_path!r}")
    else:
        client = chromadb.EphemeralClient()
        print("ChromaDB: in-memory (ephemeral) client")
    return client


def load_into_chromadb(
    chunks: List[Chunk],
    embeddings: List[List[float]],
    client,
    collection_name: str = COLLECTION_NAME,
) -> "chromadb.Collection":
    """
    Loads chunks + embeddings into a ChromaDB collection.

    DEDUPLICATION STRATEGY:
        Use chunk_id as the ChromaDB document ID. If you run this script
        twice, ChromaDB will raise an error on duplicate IDs. Catch this
        and give a clear message. Use --reset flag to wipe and reload.

    METADATA STORED PER CHUNK:
        - source_doc:    which file this came from (for source attribution)
        - chunk_index:   position in the document (for ordered retrieval)
        - word_count:    useful for filtering very short/long chunks
        - char_start/end: lets you extract exact passage from original doc

    HOW CHROMADB STORES THIS:
        Internally it uses an SQLite DB + HNSW index.
        The HNSW index is what makes approximate nearest-neighbor search fast.
    """
    # Get or create the collection
    # distance_function="cosine" is correct for sentence-transformer embeddings
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    print(f"\n Loading into ChromaDB collection: {collection_name!r}")
    print(f"   Existing items before load: {collection.count()}")

    # Prepare parallel lists for ChromaDB's add() method
    ids        = [c.chunk_id for c in chunks]
    documents  = [c.text for c in chunks]
    metadatas  = [
        {
            "source_doc":   c.source_doc,
            "chunk_index":  c.chunk_index,
            "word_count":   c.word_count,
            "char_start":   c.char_start,
            "char_end":     c.char_end,
            "total_chunks": c.total_chunks_in_doc,
        }
        for c in chunks
    ]

    # Load in batches to avoid memory issues with large document
    LOAD_BATCH = 100
    for i in range(0, len(chunks), LOAD_BATCH):
        collection.add(
            ids=ids[i : i + LOAD_BATCH],
            embeddings=embeddings[i : i + LOAD_BATCH],
            documents=documents[i : i + LOAD_BATCH],
            metadatas=metadatas[i : i + LOAD_BATCH],
        )

    final_count = collection.count()
    print(f"   ✓ Items after load: {final_count}")
    return collection


# ─────────────────────────────────────────────────────────────
# Retrieval (smoke test + future use)
# ─────────────────────────────────────────────────────────────

def query_collection(
    collection,
    model: SentenceTransformer,
    query: str,
    n_results: int = 3,
    filter_doc: str = None,
) -> dict:
    """
    Runs a search query against the loaded collection.
    This is the retriever that will get called eventually.

    Args:
        collection:  loaded ChromaDB collection
        model:       the same embedding model used at load time (IMPORTANT)
        query:       natural language question or scenario description
        n_results:   how many chunks to return
        filter_doc:  optional — restrict results to one source document

    Returns:
        dict with keys: documents, metadatas, distances, ids

    HOW TO INTERPRET RESULTS:
        - distances: cosine distance (0 = identical, 2 = opposite)
        - Typical "good" retrieval: distance < 0.5
        - Typical "weak" retrieval: distance > 1.0
        - If all results have distance > 1.2, the query doesn't match the corpus
    """
    query_embedding = model.encode([query]).tolist()

    where_filter = {"source_doc": filter_doc} if filter_doc else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )
    return results


def print_query_results(results: dict, query: str):
    """Pretty-print retrieval results for manual inspection."""
    print(f"\n Query: {query!r}")
    print(f"   Top {len(results['ids'][0])} results:\n")
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        relevance = "strong" if dist < 0.5 else "moderate" if dist < 1.0 else "weak"
        print(f"  [{i+1}] Source: {meta['source_doc']}  |  "
              f"Chunk: {meta['chunk_index']}  |  "
              f"Distance: {dist:.4f}  {relevance}")
        print(f"       {doc[:200]!r}{'...' if len(doc) > 200 else ''}\n")


# ─────────────────────────────────────────────────────────────
# Built-in tests  (run with: python  embed_load.py --test)
# ─────────────────────────────────────────────────────────────

def run_tests():
    """
    HOW TO VERIFY EMBEDDING + LOADING IS WORKING
    ==============================================
    These tests use synthetic data so you don't need real corpus files.
    Run after every change to the embedding or loading logic.

    Test philosophy:
      - Don't test that the MODEL works (it does — it's pretrained)
      - DO test that YOUR PIPELINE correctly wires model → ChromaDB
      - DO test that retrieval returns semantically relevant results
        (this catches config errors like wrong distance metric)

    Pass criteria:
          Collection count matches chunk count → no data was dropped
          Semantic retrieval works → embeddings loaded in correct order
          Metadata present → ChromaDB received all fields
          Dedup works → re-load doesn't crash or double-count
          Similar text scores lower distance than dissimilar text
    """
    print("=" * 60)
    print("RUNNING EMBED + LOAD TESTS")
    print("=" * 60)
    passed = 0
    failed = 0

    def assert_test(name: str, condition: bool, detail: str = ""):
        nonlocal passed, failed
        if condition:
            print(f"    PASS  {name}")
            passed += 1
        else:
            print(f"     FAIL  {name}" + (f"\n          {detail}" if detail else ""))
            failed += 1

    # ── Setup: synthetic chunks ───────────────────────────────
    from chunker import Chunk, split_into_chunks

    # These texts are deliberately on different topics so retrieval can distinguish between them
    SYNTHETIC_DOCS = [
        ("stats_power",
         "Statistical power is the probability of detecting a true effect when it exists. "
         "Low power leads to false negatives in A/B tests. Power depends on sample size, "
         "effect size, and alpha. Most teams target 80% power as a minimum threshold. "
         "Underpowered tests should be extended rather than called early. " * 6),

        ("peeking_bias",
         "Peeking at A/B test results before the planned end date inflates false positive rates. "
         "Each intermediate look adds to the family-wise error rate. Sequential testing methods "
         "like SPRT and always-valid inference correct for this problem. "
         "Most organizations should use a fixed horizon design with pre-committed stopping rules. " * 6),

        ("novelty_effect",
         "The novelty effect occurs when users interact with a new feature simply because it is "
         "new rather than because it is better. This inflates short-term metrics. "
         "Novelty effects typically decay within 1-3 weeks. "
         "Segment by new vs returning users to detect novelty contamination. " * 6),
    ]

    all_test_chunks: List[Chunk] = []
    for doc_name, text in SYNTHETIC_DOCS:
        chunks = split_into_chunks(text, doc_name, chunk_size=300, overlap=60)
        all_test_chunks.extend(chunks)

    print(f"\n  Using {len(all_test_chunks)} synthetic chunks across "
          f"{len(SYNTHETIC_DOCS)} mock documents\n")

    # ── Load model ────────────────────────────────────────────
    print("[1] Model loading")
    try:
        model = load_embedding_model()
        assert_test("Model loads without error", True)
        embed_dim = model.get_embedding_dimension()
        assert_test("Embedding dimension is 384 (all-MiniLM-L6-v2)",
                    embed_dim == 384,
                    f"Got {embed_dim}")
    except Exception as e:
        assert_test("Model loads without error", False, str(e))
        print("\n  ⚠️  Model failed to load. Cannot continue tests.")
        return False

    # ── Embedding ─────────────────────────────────────────────
    print("\n[2] Embedding")
    embeddings = embed_chunks(all_test_chunks, model)
    assert_test("Embedding count matches chunk count",
                len(embeddings) == len(all_test_chunks),
                f"Got {len(embeddings)} embeddings for {len(all_test_chunks)} chunks")
    assert_test("Each embedding is a list",
                all(isinstance(e, list) for e in embeddings))
    assert_test("Embeddings have correct dimension",
                all(len(e) == 384 for e in embeddings),
                f"First embedding has dim {len(embeddings[0]) if embeddings else 'N/A'}")
    assert_test("Embedding values are floats",
                all(isinstance(v, float) for v in embeddings[0][:10]))

    # ── ChromaDB loading ──────────────────────────────────────
    print("\n[3] ChromaDB loading")
    client = get_chroma_client(persist=False)  # always use in-memory for tests
    collection = load_into_chromadb(
        all_test_chunks, embeddings, client, collection_name="test_kb"
    )

    assert_test("Collection was created",
                collection is not None)
    assert_test("Collection item count matches chunk count",
                collection.count() == len(all_test_chunks),
                f"Collection has {collection.count()}, expected {len(all_test_chunks)}")

    # ── Metadata integrity ────────────────────────────────────
    print("\n[4] Metadata integrity")
    sample = collection.get(limit=1, include=["metadatas", "documents"])
    assert_test("Get returns 1 result", len(sample["ids"]) == 1)
    meta = sample["metadatas"][0]
    required_fields = ["source_doc", "chunk_index", "word_count", "char_start",
                       "char_end", "total_chunks"]
    for field in required_fields:
        assert_test(f"Metadata has '{field}' field", field in meta,
                    f"Fields present: {list(meta.keys())}")

    # ── Semantic retrieval ────────────────────────────────────
    print("\n[5] Semantic retrieval quality")

    # Query about statistical power → should hit stats_power doc
    power_results = query_collection(collection, model, "sample size and statistical power", n_results=3)
    top_source_power = power_results["metadatas"][0][0]["source_doc"]
    assert_test(
        "Query 'statistical power' retrieves from stats_power doc",
        top_source_power == "stats_power",
        f"Top result came from: {top_source_power!r}"
    )

    # Query about peeking → should hit peeking_bias doc
    peek_results = query_collection(collection, model, "looking at results before test ends", n_results=3)
    top_source_peek = peek_results["metadatas"][0][0]["source_doc"]
    assert_test(
        "Query 'looking at results early' retrieves from peeking_bias doc",
        top_source_peek == "peeking_bias",
        f"Top result came from: {top_source_peek!r}"
    )

    # Distance sanity: relevant result should have lower distance than irrelevant
    power_top_dist = power_results["distances"][0][0]
    assert_test(
        "Top retrieval distance is reasonable (< 0.8 for synthetic data)",
        power_top_dist < 0.8,
        f"Top distance was {power_top_dist:.4f} — embeddings may not be loading correctly"
    )

    # ── Deduplication ─────────────────────────────────────────
    print("\n[6] Deduplication")
    try:
        # ChromaDB raises ValueError on duplicate IDs — we want to handle this gracefully
        collection.add(
            ids=[all_test_chunks[0].chunk_id],    # same ID as already loaded
            embeddings=[embeddings[0]],
            documents=[all_test_chunks[0].text],
            metadatas=[{"source_doc": "duplicate_test", "chunk_index": 0,
                        "word_count": 5, "char_start": 0, "char_end": 10, "total_chunks": 1}],
        )
        # If we got here, ChromaDB silently accepted the duplicate (version-dependent)
        assert_test("ChromaDB handles duplicate IDs",
                    collection.count() == len(all_test_chunks),
                    "Duplicate was added — count increased")
    except Exception:
        # ChromaDB raised an error — expected behavior, count unchanged
        assert_test("ChromaDB rejects duplicate IDs (correct behavior)",
                    collection.count() == len(all_test_chunks))

    # ── Results ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("  All tests passed! Embedding pipeline is ready.")
        print("  Next: run with --persist to build the production DB.")
    else:
        print("  ⚠️  Fix failing tests before integrating with the retriever.")
    print("=" * 60)
    return failed == 0


# ─────────────────────────────────────────────────────────────
# CLI entrypoint
# ─────────────────────────────────────────────────────────────

def main(persist: bool = False, query: str = None):
    """Full pipeline: chunk → embed → load → optional test query."""
    from chunker import chunk_corpus, print_chunk_summary

    # Step 1: Load and chunk corpus
    chunks = chunk_corpus(CORPUS_FOLDER)
    print_chunk_summary(chunks)

    # Step 2: Load embedding model
    model = load_embedding_model()

    # Step 3: Embed
    embeddings = embed_chunks(chunks, model)

    # Step 4: Load into ChromaDB
    client = get_chroma_client(persist=persist)
    collection = load_into_chromadb(chunks, embeddings, client)


    print(f"   Collection '{COLLECTION_NAME}' contains {collection.count()} chunks.")
    if persist:
        print(f"   Persisted to: {CHROMA_DB_PATH}/")
        print(f"   Run: ls -lh {CHROMA_DB_PATH}/ to verify")
    else:
        print("   (In-memory only — use --persist for production)")

    # Optional: run a test query
    if query:
        results = query_collection(collection, model, query)
        print_query_results(results, query)

    return collection, model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ExperimentIQ: embed + load ChromaDB")
    parser.add_argument("--test", action="store_true", help="Run built-in tests")
    parser.add_argument("--persist", action="store_true", help="Use persistent ChromaDB")
    parser.add_argument("--query", type=str, help="Run a test retrieval query after loading")
    args = parser.parse_args()

    if args.test:
        success = run_tests()
        exit(0 if success else 1)

    main(persist=args.persist, query=args.query)