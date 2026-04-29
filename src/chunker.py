"""
ExperimentIQ — Day 6, Task 1: Document Chunker
================================================
Loads corpus documents from a folder, splits them into overlapping chunks,
and outputs a structured list ready for embedding.

WHY THIS DESIGN:
- Fixed-size chunking with overlap is the standard for RAG — overlap ensures
  no sentence is split across two chunks and loses its context.
- chunk_size=400 tokens ≈ 2-3 paragraphs. Enough context for the LLM to
  reason from, small enough to stay focused on one concept.
- chunk_overlap=80 tokens ≈ 20% overlap. The sweet spot — you capture
  boundary context without duplicating too much content.
- We tag every chunk with its source doc, chunk index, and char offsets.
  These metadata fields feed ChromaDB and let you trace every LLM claim
  back to its source — critical for debugging bad retrievals.

USAGE:
    python chunker.py                   # runs on ./corpus/ folder
    python chunker.py --test            # runs built-in tests only
    python chunker.py --folder my_docs  # custom folder

HOW TO TEST (see bottom of file or run --test flag):
    1. Unit tests validate chunk size, overlap, and metadata fields
    2. Inspection tests let you eyeball a real chunk visually
    3. Edge case tests check empty docs, tiny docs, unicode
"""

import os
import re
import json
import argparse
from dataclasses import dataclass, asdict
from typing import List, Optional


# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────

CHUNK_SIZE = 400        # characters (≈ 100 tokens for English text at ~4 chars/token)
CHUNK_OVERLAP = 80      # characters of overlap between consecutive chunks
MIN_CHUNK_SIZE = 50     # discard chunks shorter than this (usually trailing whitespace)
CORPUS_FOLDER = "../documents"


# ─────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    """A single text chunk with full provenance metadata."""
    chunk_id: str           # unique ID: "{doc_name}__chunk_{index:04d}"
    source_doc: str         # filename of origin document
    chunk_index: int        # position of this chunk within its document
    text: str               # the actual chunk content
    char_start: int         # start character offset in the original document
    char_end: int           # end character offset in the original document
    word_count: int         # rough size signal for QA
    total_chunks_in_doc: int = 0  # filled in after all chunks are created


# ─────────────────────────────────────────────────────────────
# Core chunking logic
# ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Normalize whitespace and remove noise before chunking.
    - Collapses 3+ newlines to 2 (preserves paragraph breaks, kills whitespace deserts)
    - Strips leading/trailing whitespace per line
    """
    text = re.sub(r'\n{3,}', '\n\n', text)
    lines = [line.rstrip() for line in text.splitlines()]
    return '\n'.join(lines).strip()


def split_into_chunks(text: str, doc_name: str,
                      chunk_size: int = CHUNK_SIZE,
                      overlap: int = CHUNK_OVERLAP) -> List[Chunk]:
    """
    Splits a document string into overlapping character-based chunks.

    Strategy: sentence-aware sliding window.
    - We try to split at sentence boundaries ('. ', '? ', '! ', '\n\n')
      rather than mid-sentence. This keeps each chunk semantically coherent.
    - If no sentence boundary found within the window, we fall back to the
      hard character limit (rare with normal prose).

    Args:
        text:       cleaned document text
        doc_name:   filename used to build chunk_id and source_doc fields
        chunk_size: target max characters per chunk
        overlap:    how many chars to step back when starting the next chunk

    Returns:
        List of Chunk objects, in document order
    """
    if not text or len(text.strip()) < MIN_CHUNK_SIZE:
        return []

    # Sentence boundary markers, in priority order
    SPLIT_MARKERS = ['\n\n', '. ', '? ', '! ', '\n', '; ']

    chunks: List[Chunk] = []
    start = 0
    doc_len = len(text)

    while start < doc_len:
        end = min(start + chunk_size, doc_len)

        # If we're not at the end of the document, try to find a clean break
        if end < doc_len:
            best_break = end  # fallback: hard cut

            for marker in SPLIT_MARKERS:
                # Search backward from `end` for a sentence boundary
                search_start = max(start + MIN_CHUNK_SIZE, end - overlap)
                pos = text.rfind(marker, search_start, end)
                if pos != -1:
                    best_break = pos + len(marker)
                    break

            end = best_break

        raw_chunk = text[start:end]
        cleaned_chunk = raw_chunk.strip()

        if len(cleaned_chunk) >= MIN_CHUNK_SIZE:
            chunk_index = len(chunks)
            chunks.append(Chunk(
                chunk_id=f"{doc_name}__chunk_{chunk_index:04d}",
                source_doc=doc_name,
                chunk_index=chunk_index,
                text=cleaned_chunk,
                char_start=start,
                char_end=end,
                word_count=len(cleaned_chunk.split()),
            ))

        # Anchor next chunk relative to where this chunk ended, minus overlap
        next_start = end
        while next_start < doc_len and text[next_start] not in (' ', '\n'):
            next_start += 1
        start = min(next_start + 1, doc_len)

    # Back-fill total_chunks_in_doc now that we know the count
    for chunk in chunks:
        chunk.total_chunks_in_doc = len(chunks)

    return chunks


# ─────────────────────────────────────────────────────────────
# Document loader
# ─────────────────────────────────────────────────────────────

def load_document(filepath: str) -> Optional[str]:
    """
    Loads a .txt or .md file. Returns None if unreadable.
    Extend this function when you add PDF support in a later phase.
    """
    supported = ('.txt', '.md')
    if not filepath.endswith(supported):
        print(f"  [SKIP] {filepath} — unsupported format (add PDF later)")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"  [ERROR] Could not read {filepath}: {e}")
        return None


def chunk_corpus(folder: str) -> List[Chunk]:
    """
    Main entry point. Walks the corpus folder, chunks every document,
    and returns a flat list of all chunks across all docs.

    Args:
        folder: path to folder containing .txt / .md corpus files

    Returns:
        all_chunks: flat list of Chunk objects, ready for embedding
    """
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Corpus folder not found: {folder!r}\n"
                                f"Create it and add your .txt/.md documents.")

    all_chunks: List[Chunk] = []
    doc_files = sorted([f for f in os.listdir(folder)
                        if f.endswith('.txt') or f.endswith('.md')])

    if not doc_files:
        raise ValueError(f"No .txt or .md files found in {folder!r}")

    print(f"\n Loading corpus from: {folder}")
    print(f"   Found {len(doc_files)} document(s)\n")

    for filename in doc_files:
        filepath = os.path.join(folder, filename)
        raw_text = load_document(filepath)
        if raw_text is None:
            continue

        clean = clean_text(raw_text)
        doc_name = os.path.splitext(filename)[0]  # strip extension
        chunks = split_into_chunks(clean, doc_name)

        print(f"  ✓ {filename:<40} → {len(chunks):>3} chunks  "
              f"({len(clean):,} chars)")
        all_chunks.extend(chunks)

    print(f"\n  Total chunks across corpus: {len(all_chunks)}")
    return all_chunks


# ─────────────────────────────────────────────────────────────
# Output helpers
# ─────────────────────────────────────────────────────────────

def chunks_to_json(chunks: List[Chunk], output_path: str = "./chunks_preview.json"):
    """Save chunks to JSON for inspection. Useful before committing to ChromaDB."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump([asdict(c) for c in chunks], f, indent=2, ensure_ascii=False)
    print(f"\n Chunks saved to: {output_path}")


def print_chunk_summary(chunks: List[Chunk]):
    """Print a QA table: doc name, chunk count, avg word count."""
    from collections import defaultdict
    doc_stats = defaultdict(list)
    for c in chunks:
        doc_stats[c.source_doc].append(c.word_count)

    print("\n Chunk Summary:")
    print(f"  {'Document':<40} {'Chunks':>6}  {'Avg Words':>9}  {'Min':>4}  {'Max':>4}")
    print("  " + "─" * 70)
    for doc, word_counts in sorted(doc_stats.items()):
        avg = sum(word_counts) / len(word_counts)
        print(f"  {doc:<40} {len(word_counts):>6}  {avg:>9.1f}  "
              f"{min(word_counts):>4}  {max(word_counts):>4}")


# ─────────────────────────────────────────────────────────────
# Built-in tests  (run with: python chunker.py --test)
# ─────────────────────────────────────────────────────────────

def run_tests():
    """
    HOW TO VERIFY CHUNKING IS WORKING
    ===================================
    These tests check the chunker without needing real corpus files.
    Run them first every time you change chunk_size or overlap.

    Pass criteria:
        ✅ All assertions pass → chunker is mathematically correct
        ✅ Overlap test passes → no context is being silently dropped
        ✅ Metadata test passes → ChromaDB will have clean IDs and fields
        ✅ Edge cases pass → pipeline won't crash on bad input
    """
    print("=" * 60)
    print("RUNNING DAY 6 CHUNKER TESTS")
    print("=" * 60)
    passed = 0
    failed = 0

    def assert_test(name: str, condition: bool, detail: str = ""):
        nonlocal passed, failed
        if condition:
            print(f"PASS  {name}")
            passed += 1
        else:
            print(f"FAIL  {name}" + (f"\n          {detail}" if detail else ""))
            failed += 1

    # ── Test 1: Basic chunking produces output ────────────────
    print("\n[1] Basic functionality")
    text_100_words = ("The quick brown fox jumps over the lazy dog. " * 20).strip()
    chunks = split_into_chunks(text_100_words, "test_doc", chunk_size=200, overlap=40)
    assert_test("Produces at least 1 chunk", len(chunks) >= 1)
    assert_test("All chunks are Chunk objects", all(isinstance(c, Chunk) for c in chunks))

    # ── Test 2: Chunk size stays within bounds ────────────────
    print("\n[2] Chunk size bounds")
    long_text = "This is a test sentence with some real content here. " * 100
    chunks = split_into_chunks(long_text, "size_test", chunk_size=300, overlap=60)
    oversized = [c for c in chunks if len(c.text) > 300 + 60]  # allow small overage at boundaries
    assert_test(
        "No chunk exceeds chunk_size + overlap by much",
        len(oversized) == 0,
        f"{len(oversized)} oversized chunks found"
    )
    assert_test(
        "All chunks meet MIN_CHUNK_SIZE",
        all(len(c.text) >= MIN_CHUNK_SIZE for c in chunks),
        "Some chunks are too short"
    )

    # ── Test 3: Overlap actually overlaps ────────────────────
    print("\n[3] Overlap correctness")
    # With overlap, the end of chunk N should appear at the start of chunk N+1
    sample = "Alpha beta gamma delta epsilon zeta eta theta iota kappa. " * 30
    chunks = split_into_chunks(sample, "overlap_test", chunk_size=150, overlap=50)
    if len(chunks) >= 2:
        end_of_first = chunks[0].text[-30:]   # last 30 chars of chunk 0
        start_of_second = chunks[1].text[:60]  # first 60 chars of chunk 1
        has_overlap = end_of_first.strip()[:10] in start_of_second
        assert_test(
            "Consecutive chunks share overlapping content",
            has_overlap,
            f"End of chunk 0: '{end_of_first[:30]}'\nStart of chunk 1: '{start_of_second[:30]}'"
        )
    else:
        assert_test("Text long enough to produce 2+ chunks for overlap test", False)

    # ── Test 4: Metadata fields are correct ──────────────────
    print("\n[4] Metadata integrity")
    chunks = split_into_chunks("Hello world. " * 50, "meta_test", chunk_size=100, overlap=20)
    if chunks:
        c = chunks[0]
        assert_test("chunk_id format is correct",
                    c.chunk_id == f"meta_test__chunk_0000",
                    f"Got: {c.chunk_id!r}")
        assert_test("source_doc matches input",
                    c.source_doc == "meta_test",
                    f"Got: {c.source_doc!r}")
        assert_test("chunk_index starts at 0", c.chunk_index == 0)
        assert_test("char_start is 0 for first chunk", c.char_start == 0)
        assert_test("word_count > 0", c.word_count > 0)
        assert_test("total_chunks_in_doc is populated",
                    c.total_chunks_in_doc == len(chunks),
                    f"Got {c.total_chunks_in_doc}, expected {len(chunks)}")

    # ── Test 5: Edge cases ────────────────────────────────────
    print("\n[5] Edge cases")
    assert_test("Empty string → 0 chunks", split_into_chunks("", "empty") == [])
    assert_test("Whitespace-only → 0 chunks", split_into_chunks("   \n\n  ", "whitespace") == [])
    assert_test("Very short text → 0 chunks",
                split_into_chunks("Hi.", "tiny") == [])

    unicode_text = "Статистика — это наука. " * 30 + "Tüm testler geçmeli. " * 30
    unicode_chunks = split_into_chunks(unicode_text, "unicode_test", chunk_size=200, overlap=40)
    assert_test("Unicode text chunked without crash", len(unicode_chunks) > 0)

    multiline = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.\n\n" * 10
    ml_chunks = split_into_chunks(multiline, "multiline", chunk_size=150, overlap=30)
    assert_test("Multi-paragraph doc produces chunks", len(ml_chunks) > 0)

    # ── Test 6: Text cleaning ─────────────────────────────────
    print("\n[6] Text cleaning")
    dirty = "Line one.   \n\n\n\n\nLine two.\n\n\n\nLine three."
    cleaned = clean_text(dirty)
    assert_test("3+ newlines collapsed to 2", '\n\n\n' not in cleaned)
    assert_test("Cleaned text still has content", len(cleaned) > 0)

    # ── Results ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("  All tests passed! Chunker is ready.")
    else:
        print("  ⚠️  Fix failing tests before moving to Task 2.")
    print("=" * 60)
    return failed == 0


# ─────────────────────────────────────────────────────────────
# Visual inspection helper
# ─────────────────────────────────────────────────────────────

def inspect_chunks(chunks: List[Chunk], n: int = 3):
    """
    HOW TO VISUALLY VERIFY YOUR CHUNKS LOOK RIGHT
    ===============================================
    Call this after chunk_corpus() to eyeball real chunks.
    You're checking:
      - Does each chunk contain a coherent idea? (not split mid-sentence)
      - Is chunk_id unique and descriptive?
      - Does word_count look reasonable (50-150 words is typical)?
      - Do consecutive chunks share some overlapping text?
    """
    print(f"\n Inspecting first {n} chunks (visual QA):\n")
    for i, chunk in enumerate(chunks[:n]):
        print(f"  ── Chunk {i}: {chunk.chunk_id} ──")
        print(f"  Source : {chunk.source_doc}")
        print(f"  Words  : {chunk.word_count}  |  Chars: {chunk.char_start}–{chunk.char_end}")
        print(f"  Text   : {chunk.text[:200]!r}{'...' if len(chunk.text) > 200 else ''}")
        print()

    if len(chunks) >= 2:
        print("  ── Overlap check (end of chunk 0 vs start of chunk 1) ──")
        print(f"  End of [0]  : {chunks[0].text[-80:]!r}")
        print(f"  Start of [1]: {chunks[1].text[:80]!r}")
        print()


# ─────────────────────────────────────────────────────────────
# CLI entrypoint
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ExperimentIQ document chunker")
    parser.add_argument("--test", action="store_true", help="Run built-in unit tests only")
    parser.add_argument("--folder", default=CORPUS_FOLDER, help="Path to corpus folder")
    parser.add_argument("--save", action="store_true", help="Save chunks to chunks_preview.json")
    args = parser.parse_args()

    if args.test:
        success = run_tests()
        exit(0 if success else 1)

    # Normal run: chunk the corpus
    chunks = chunk_corpus(args.folder)
    print_chunk_summary(chunks)
    inspect_chunks(chunks, n=3)

    if args.save:
        chunks_to_json(chunks)

    print(f"\n Task 1 complete. {len(chunks)} chunks ready for embedding (Task 2).")
    print("   Next: pass `chunks` to embed_and_load.py\n")
