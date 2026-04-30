"""
retriever.py
============
Retrieves the most relevant knowledge base chunks from ChromaDB
given a natural language test scenario.

Usage:
    from embed_load import load_embedding_model, get_chroma_client, COLLECTION_NAME
    from retriever import retrieve_context

    model      = load_embedding_model()
    client     = get_chroma_client(persist=True)
    collection = client.get_collection(COLLECTION_NAME)

    results = retrieve_context("checkout flow A/B test, p=0.03, underpowered", collection, model)
"""

def retrieve_context(scenario_text: str, collection, model, n_results: int = 5) -> list[dict]:
    """
    Embeds scenario_text and queries ChromaDB for the top-n most similar chunks.

    Parameters
    ----------
    scenario_text : str
        Natural language summary of the A/B test scenario.
        e.g. "checkout flow A/B test, one-tailed superiority, p=0.03, underpowered, 14 days"
    collection : chromadb.Collection
        Live ChromaDB collection object (already loaded by caller).
    model : SentenceTransformer
        Embedding model (same one used to embed the knowledge base).
    n_results : int
        Number of top chunks to return. Default is 5.

    Returns
    -------
    list of dicts with keys: text, doc_name, chunk_index, similarity_score
    """

    # STEP 1 — Embed the query
    # model.encode() returns a numpy array — ChromaDB needs a plain Python list
    query_vector = model.encode(scenario_text).tolist()

    # STEP 2 — Query ChromaDB
    # ChromaDB returns cosine DISTANCE (0 = identical, 2 = opposite)
    raw = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    # STEP 3 — Parse and reshape results
    # ChromaDB wraps everything in an extra list (one per query submitted)
    # We only submitted one query, so we take index [0] from each
    documents = raw["documents"][0]
    metadatas = raw["metadatas"][0]
    distances = raw["distances"][0]

    # STEP 4 — Build clean output
    # Convert cosine distance → cosine similarity: similarity = 1 - distance
    results = []
    for text, meta, distance in zip(documents, metadatas, distances):
        results.append({
            "text":             text,
            "doc_name":         meta.get("source_doc", "unknown"),
            "chunk_index":      meta.get("chunk_index", -1),
            "similarity_score": round(1 - distance, 4)
        })

    # Results come back sorted by distance ascending (most similar first)
    # After converting to similarity, order is now similarity descending — correct
    return results
